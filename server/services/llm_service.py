from openai import OpenAI
import dotenv
import os
import json
import pathlib
# Generate an explanation of the topic in the style of the celebrity
def generate_explanation(persona_id, query):
    """Generate an explanation of the topic in the style of the celebrity"""

    # Load environment variables
    dotenv.load_dotenv()

    # Set OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Load personas data
    current_dir = pathlib.Path(__file__).parent.parent
    personas_path = os.path.join(current_dir, "data", "personas.json")

    # Load personas data
    with open(personas_path, "r") as f:
        personas = json.load(f)

    # Find the persona with the given id
    persona = next((p for p in personas["personas"] if p["id"] == persona_id), None)

    # If persona is not found, return an error
    if not persona:
        return "Persona not found"

    # Get the persona's style
    style = persona["style_prompt"]
    name = persona["name"]

    # Generate the explanation
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a brilliant writer who is capable of writing in the style of any person or celebrity. You are given a query and a style prompt. You need to write an explanation of the query in the style of the celebrity."},
            {"role": "user", "content": f"""
                I want you to write a speech in the style of {name}. It should be about 30-50 seconds long, with a hard cap of 60 seconds.
                I want you to explain the following in great detail: {query}
                Speak in the following style: {style}. Overall, it's incredibly important to really dive deep into explaining the concepts at a low level. You are a brilliant teacher, so don't hold back.
            """}
        ]
    )
    
    # Get the response
    return response.choices[0].message.content