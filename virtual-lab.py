import os
from flask import Flask, request, render_template
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/experiment', methods=['POST'])
def experiment():
    user_input = request.form['user_input']
    try:
        response = client.completions.create(
            model="text-davinci-003",
            prompt=user_input,
            max_tokens=100
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) # This is how the $PORT is obtained
    app.run(host='0.0.0.0', port=port)  #  Binding to 0.0.0.0 for heroku and using the $PORT
