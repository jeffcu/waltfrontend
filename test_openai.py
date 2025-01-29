import openai
import os

# Set the OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    # Test the API by making a simple call
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Test if OpenAI API is working."},
            {"role": "user", "content": "Hello, are you working?"}
        ]
    )
    print("Success! API is working.")
    print("Response:", response.choices[0].message["content"])
except openai.AuthenticationError:
    print("Authentication failed! Check your API key.")
except openai.OpenAIError as e:
    print(f"API Error: {e}")
