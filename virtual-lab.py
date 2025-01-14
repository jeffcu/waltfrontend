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

@app.route('/', methods=['GET', 'POST'])
def home():
    """Renders the main page with the user prompt input and displays the response."""
    user_input = ""
    response = ""
    error = ""
    system_instructions = "" # set an initial empty string for the system instructions

    if request.method == 'POST':
        user_input = request.form['user_input'] # get the user input from the form
        system_instructions = request.form.get('system_instructions', "") # get the system instructions, but default to an empty string

        if len(user_input.split()) > 256:
            error = "Error: Input must be less than 256 words."
            return render_template('index.html', error=error, user_input=user_input, system_instructions=system_instructions)


        combined_prompt = f"{system_instructions}\n\nUser Input: {user_input}" # combine the instructions and user input

        try:
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=combined_prompt, # use the combined prompt
                max_tokens=150,
                temperature=0.7
            )
            response = response.choices[0].text.strip() # get the response
        except Exception as e:
           error = str(e) # catch any errors

        return render_template('index.html', response=response, user_input=user_input, system_instructions=system_instructions, error=error) # Render the response and user_input

    return render_template('index.html', response=response, user_input=user_input, system_instructions=system_instructions, error=error) # render the template

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
