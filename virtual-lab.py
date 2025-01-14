import os
from flask import Flask, request, render_template
from openai import OpenAI
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/experiment', methods=['POST'])
def experiment():
    user_input = request.form['user_input']
    if len(user_input.split()) > 256:
      return "Error: Input must be less than 256 words."
    try:
        response = client.completions.create(
            model="text-davinci-003",
            prompt=user_input,
            max_tokens=150, # set to 150 for this
            temperature=0.7 # added a temperature parameter
        )
        return render_template('index.html', response=response.choices[0].text.strip(), user_input=user_input)
    except Exception as e:
        return render_template('index.html', error=str(e), user_input=user_input)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
