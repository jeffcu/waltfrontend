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

@app.route('/', methods=['GET', 'POST']) # allow for get and post methods
def home():
    """Renders the main page with the user prompt input and displays the response."""
    user_input = "" # set an initial empty string for user input
    response = "" # set an initial empty string for the response
    error = "" # set an initial empty string for errors

    if request.method == 'POST': # check to see if we have received a post request
        user_input = request.form['user_input'] # get the user input from the form
        if len(user_input.split()) > 256:
           error = "Error: Input must be less than 256 words." # set the error message
           return render_template('index.html', error=error, user_input=user_input) # render template with the error

        try:
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=user_input,
                max_tokens=150,
                temperature=0.7
            )
            response = response.choices[0].text.strip() # set the response
        except Exception as e:
           error = str(e) # If there is an error store that as the error string

    return render_template('index.html', response=response, user_input=user_input, error=error) # render the template
if __name__ == '__main__':
    # Get the port from environment variable or default to 5000 locally
    port = int(os.environ.get('PORT', 5000))
    # Run the flask app
    app.run(host='0.0.0.0', port=port)
