from flask import Flask, request, render_template
import openai
import os
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/experiment', methods=['POST'])
def experiment():
    user_input = request.form['user_input']
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_input,
            max_tokens=100
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
