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
    pass

# Assemble all of these into a video 
def assemble_visuals(visuals):
    pass
