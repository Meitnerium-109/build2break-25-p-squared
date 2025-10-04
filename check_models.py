import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the environment variables from your .env file
load_dotenv()

# Configure the API key from the loaded environment variable
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Make sure your .env file is set up correctly.")
genai.configure(api_key=api_key)

print("--- Models Available to Your API Key ---")
print("These are the models that support 'generateContent':")
print("-" * 40)

try:
    # The genai.list_models() call asks Google's servers for the list.
    # We then loop through them and check if they support the 'generateContent' method.
    for m in genai.list_models():
      if 'generateContent' in m.supported_generation_methods:
        print(m.name)
except Exception as e:
    print(f"An error occurred while trying to list models: {e}")
    print("Please double-check that your API key is correct and has the 'Generative Language API' enabled in your Google Cloud project.")


print("-" * 40)