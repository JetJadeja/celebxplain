import json
import os
import dotenv
from typing import List, Literal
from pydantic import BaseModel
import requests
from PIL import Image
import numpy as np
import cv2
from openai import OpenAI
import subprocess
import io
import tempfile
import shutil
import re


class VisualSegment(BaseModel):
    type: Literal["animation", "image"]
    description: str
    start_time: float
    end_time: float

class VisualPlan(BaseModel):
    segments: List[VisualSegment]

# Create the visuals for the video
def create_explanatory_visuals(transcription, output_dir):
    # First, let's create a visual plan
    visual_plan = create_visual_plan(transcription)
    print(visual_plan)
    
    # Ensure output directory exists
    # os.makedirs(output_dir, exist_ok=True)
    
    # TODO: Implement visual creation using the plan
    # visuals = create_visuals(visual_plan)
    # final_video = assemble_visuals(visuals)
    
    # For now, let's just save the visual plan
    # with open(os.path.join(output_dir, "visual_plan.json"), "w") as f:
    #     f.write(visual_plan.model_dump_json(indent=2))
    
    return visual_plan

# Create the visual plan
def create_visual_plan(transcription):
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Analyze this transcript and create a detailed visual plan for a video."},
            {"role": "user", "content": f"""
             
            {json.dumps(transcription, indent=2)}
            
            Above, I have a transcript with timestamps. Please analyze it and create a detailed visual plan.
            
            Break the explanation into logical segments and for each segment, suggest either:
            - An animation (for complex concepts, processes, or math)
            - An image (for simpler illustrations or examples)
            
            Specify exact start_time and end_time for each visual and provide a clear, detailed description of what to display.

            It's crucial to remember that a person will already be narrating the content. Your task is to create a secondary, simple presentation next to them. Focus on illustrating on-paper concepts or topics suitable for 2D animations in the style of 3Blue1Brown.
            For example, use static images for straightforward visual references like, "Hey, look at this pool. Let's calculate the area of this pool." These should be simple and direct.
            Use animations specifically for visualizing mathematical concepts, such as illustrating the area under a curve for integration. Keep these animations simple and flat, emphasizing clarity and understanding over complexity.
            Please ensure that your designs are clear, simple, and help convey mathematical ideas without unnecessary complexity. Our goal is to make the concepts accessible and easy to understand.
            """}
        ],
        response_format=VisualPlan,
    )
    
    return completion.choices[0].message.parsed

# Create the visuals one by one
def create_visuals(visual_plan):
    pass

# Assemble the visuals into a final video
def assemble_visuals(visuals):
    pass

# Create static image for video
def create_static_image(description, length, id, output_dir):
    # Setup OpenAI client
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, f"{id}.mp4")
    
    try:
        # Generate image using DALL-E
        response = client.images.generate(
            model="dall-e-3",
            prompt=description,
            n=1,
            size="1024x1024",
        )
        
        # Get the image URL
        image_url = response.data[0].url
        
        # Download the image data
        image_data = requests.get(image_url).content
        
        # Load image directly from memory without saving to disk
        img = Image.open(io.BytesIO(image_data))
        
        # Get image dimensions
        width, height = img.size
        
        # Convert image to numpy array
        img_array = np.array(img)
        
        # Create a video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30
        video = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        
        # Write the same frame for the duration of the video
        for _ in range(int(fps * length)):
            # Convert RGB to BGR (OpenCV uses BGR)
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                frame = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                frame = img_array
            video.write(frame)
        
        video.release()
        
        print(f"Created static image video at {video_path}")
        return video_path
    
    except Exception as e:
        print(f"Error creating static image: {e}")
        return None

# Create an animation
def create_animation(description, length, id, output_dir):
    """
    Creates a matplotlib animation based on a description.
    
    Args:
        description: Description of what the animation should show
        length: Desired length of the animation in seconds
        id: Unique identifier for the animation
        output_dir: Directory to save the final animation
        
    Returns:
        Path to the created animation video file or None if failed
    """
    # Setup OpenAI client
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, f"{id}.mp4")
    
    try:
        # Step 1: Generate Matplotlib animation code
        animation_code = generate_matplotlib_code(client, description, length)
        if not animation_code:
            return None
        
        # Step 2: Try-Fix-Retry loop
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"Attempt {attempt+1}/{max_attempts} to execute animation code")
            
            # Try to execute the code
            animation_path, error_message = execute_matplotlib_code(animation_code, length, id, output_dir)
            
            # If successful, we're done
            if animation_path:
                print(f"Created animation at {animation_path}")
                return animation_path
            
            # Print the error message
            print(error_message)
            
            # If failed and we have more attempts, try to fix the code
            if attempt < max_attempts - 1 and error_message:
                print(f"Fixing code based on error message...")
                animation_code = fix_matplotlib_code(client, animation_code, error_message, description, length)
                if not animation_code:
                    print("Failed to fix the code. Giving up.")
                    return None
        
        print(f"Failed to create animation after {max_attempts} attempts")
        return None
        
    except Exception as e:
        print(f"Error creating animation: {e}")
        return None

def generate_matplotlib_code(client, description, length):
    """
    Uses OpenAI to generate Matplotlib animation code based on the description.
    
    Args:
        client: OpenAI client
        description: Description of the animation
        length: Target length in seconds
        
    Returns:
        Generated Matplotlib animation code as a string or None if failed
    """
    prompt = f"""
    Create Python code using Matplotlib's animation module to generate a mathematical animation.
    
    The animation should be approximately {length} seconds long.
    
    Requirements:
    1. Use matplotlib.animation.FuncAnimation for the animation
    2. Include all necessary imports (matplotlib.pyplot, matplotlib.animation, numpy, etc.)
    3. Set the animation to run for exactly {length} seconds (fps = 30)
    4. Make sure to use a proper save function that works with FFMpegWriter or PillowWriter
    5. The code should be complete and self-contained
    6. Include clear, descriptive comments
    7. Use a clean, minimalist visual style similar to 3Blue1Brown's animations
    8. Make sure text is readable and appropriately sized
    9. For mathematical expressions, use LaTeX formatting with plt.text() and the r'$...$' syntax
    10. The code should NOT rely on showing the animation with plt.show() - it MUST save to a file
    11. Avoid using deprecated Matplotlib features
    12. Use "plt.style.use('dark_background')"
    
    The animation should visualize the following concept:
    {description}. 
    
    Return ONLY the Python code with no additional explanations.
    """
    
    try:
        response = client.chat.completions.create(
            model="o3-mini-2025-01-31",
            messages=[
                {"role": "system", "content": "You are an expert in mathematical animations and Python programming."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the code from the response
        code = response.choices[0].message.content
        
        # Clean the code (remove markdown code blocks if present)
        code = re.sub(r'^```python\s*', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\s*$', '', code, flags=re.MULTILINE)
        
        return code
        
    except Exception as e:
        print(f"Error generating Matplotlib code: {e}")
        return None

def execute_matplotlib_code(code, length, id, output_dir):
    """
    Executes the generated Matplotlib animation code.
    
    Args:
        code: The matplotlib animation code to execute
        length: Desired animation length in seconds
        id: Unique identifier for the animation
        output_dir: Directory to save the animation
        
    Returns:
        Tuple of (path_to_animation, error_message)
        If successful, error_message will be None
        If failed, path_to_animation will be None
    """
    try:
        # Create a temporary directory for our files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare the output path
            output_path = os.path.join(output_dir, f"{id}.mp4")
            
            # Modify the code to ensure it saves to the correct path
            # This replaces any existing output path with our desired path
            modified_code = re.sub(
                r'(anim\.save\([\'"])[^\'"]+([\'"])',
                f'\\1{output_path}\\2',
                code
            )
            
            if 'anim.save' not in modified_code:
                # If no save command is found, add one at the end
                modified_code += f'\n\n# Save the animation\nanim.save("{output_path}", writer="ffmpeg", fps=30, dpi=200)\n'
            
            # Save the modified code to a temporary file
            script_path = os.path.join(temp_dir, "animation_script.py")
            with open(script_path, "w") as f:
                f.write(modified_code)
            
            # Execute the script
            process = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if the execution was successful
            if process.returncode != 0:
                error_message = f"Script execution failed:\nSTDOUT: {process.stdout}\nSTDERR: {process.stderr}"
                return None, error_message
            
            # Check if the output file was created
            if os.path.exists(output_path):
                return output_path, None
            else:
                return None, "Animation was executed but no output file was created"
    
    except Exception as e:
        import traceback
        error_message = f"Error executing Matplotlib code: {e}\n{traceback.format_exc()}"
        return None, error_message

def fix_matplotlib_code(client, code, error_message, original_description, length):
    # First, let's get some reasoning about the error
    try: 
        reasoning_prompt = f"""
        I'm having an issue with my Matplotlib animation code. Please explain what's wrong and how to fix it.

        Error message:
        {error_message}

        Here's the code:
        ```python
        {code}
        ```

        Please explain the exact error and how I should fix it.
        """
        
        reasoning_response = client.chat.completions.create(
            model="o3-mini-2025-01-31",
            messages=[
                {"role": "system", "content": "You are an expert in Python programming and Matplotlib animations."},
                {"role": "user", "content": reasoning_prompt}
            ]
        )
        
        reasoning = reasoning_response.choices[0].message.content
        print("Error analysis:\n", reasoning)

    except Exception as e:
        print(f"Error analyzing Matplotlib code: {e}")
        reasoning = "Unable to analyze the error. Will attempt to fix common issues."
    
    # Now, let's fix the code
    fix_prompt = f"""
    You are an expert in Matplotlib animations and debugging Python code.
    
    I tried to generate and execute a Matplotlib animation but encountered an error.
    
    Original animation description:
    {original_description}
    
    Here's the error message:
    ```
    {error_message}
    ```

    Here's the code that was generated:
    ```python
    {code}
    ```
    
    Analysis of the error:
    {reasoning}
    
    IT IS CRITICAL THAT YOU FIX THE CODE COMPLETELY AND CORRECTLY THIS TIME. IT'S ESSENTIAL THAT THE CODE IS CORRECT.
    SOMETIMES IT IS OPTIMAL TO REWRITE THE CODE ENTIRELY RATHER THAN ATTEMPTING TO FIX THE SMALL ISSUES IN THE CURRENT CODE.

    Make sure the animation:
    1. Is exactly {length} seconds long
    2. Properly saves to a file (don't use plt.show())
    3. Uses appropriate DPI and quality settings
    
    Return ONLY the fixed Python code with no additional explanations.
    """
    
    try:
        response = client.chat.completions.create(
            model="o3-mini-2025-01-31",
            messages=[
                {"role": "system", "content": "You are an expert in mathematical animations and Python programming."},
                {"role": "user", "content": fix_prompt}
            ]
        )
        
        # Extract the fixed code from the response
        fixed_code = response.choices[0].message.content
        
        # Clean the code (remove markdown code blocks if present)
        fixed_code = re.sub(r'^```python\s*', '', fixed_code, flags=re.MULTILINE)
        fixed_code = re.sub(r'^```\s*$', '', fixed_code, flags=re.MULTILINE)
        
        return fixed_code
        
    except Exception as e:
        print(f"Error fixing Matplotlib code: {e}")
        return None