import openai
import os

# Create an OpenAI client with the API key
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

try:
    # Test the API by making a simple request
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Test if OpenAI API is working."},
            {"role": "user", "content": "Hello, are you working?"}
        ]
    )
    print("✅ Success! API is working.")
    print("🔹 Response:", response.choices[0].message.content)
except openai.AuthenticationError:
    print("❌ Authentication failed! Check your API key.")
except Exception as e:
    print(f"⚠️ API Error: {e}")
