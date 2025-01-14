import os
from flask import Flask, request, render_template
from openai import OpenAI
from dotenv import load_dotenv

# Load the API key from .env file (for local testing)
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Flask application
app = Flask(__name__)

@app.route('/')
def home():
    """Renders the main page with the user prompt input."""
    return render_template('index.html')

@app.route('/experiment', methods=['POST'])
def experiment():
    """Handles the user prompt input, sends it to OpenAI, and displays the response."""
    user_input = request.form['user_input'] # get input
    if len(user_input.split()) > 256:
        return render_template('index.html', error="Error: Input must be less than 256 words.", user_input=user_input)
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct", # Specify the model
            prompt=user_input, # prompt to send to the api
            max_tokens=150, # Max tokens from the api
            temperature=0.7 # temperature parameter
        )
        # Send the response back to the index.html to be displayed
        return render_template('index.html',
                                response=response.choices[0].text.strip(),
                                user_input=user_input)
    except Exception as e:
      # If there is an error send that back to the index.html
      return render_template('index.html', error=str(e), user_input=user_input)


if __name__ == '__main__':
    # Get the port from environment variable or default to 5000 locally
    port = int(os.environ.get('PORT', 5000))
    # Run the flask app
    app.run(host='0.0.0.0', port=port)
