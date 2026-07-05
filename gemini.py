from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

def ask_gemini(prompt: str) -> str:
    interaction = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        system_instruction="Respond in less than 4000 characters."
    )
    return interaction.output_text

if(__name__ == "__main__"):
    prompt = "Write a poem about a lonely robot who wants to be human."
    response = ask_gemini(prompt)
    print(response)
