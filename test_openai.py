import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    response = openai.Model.list()
    print("Success! Models available:", [m.id for m in response["data"]])
except openai.error.AuthenticationError:
    print("Authentication failed! Check your API key.")
except openai.error.OpenAIError as e:
    print(f"API Error: {e}")
