import os
from flask import Flask, request, render_template
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from PyPDF2 import PdfReader
import fitz  # PyMuPDF

# Load the API key from .env file (for local testing)
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to store uploaded files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Application version
APP_VERSION = "0.0.9"

async def call_openai_api(prompt):
    """Asynchronous function to call OpenAI API with a prompt."""
    try:
        response = client.completions.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def extract_text_from_file(filepath):
    """Extract text content from supported file types."""
    if filepath.endswith('.pdf'):
        try:
            # Attempt with PyPDF2
            reader = PdfReader(filepath)
            text = "\n".join([page.extract_text() for page in reader.pages])
            if text.strip():
                return text
            # Fallback to PyMuPDF
            with fitz.open(filepath) as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    else:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def home():
    """Renders the main page with the user query input and displays the inputs, API call, and response."""
    inputs = {}
    api_call_text = ""
    api_response = ""
    error = ""

    if request.method == 'POST':
        try:
            # Capture user inputs
            meta_instructions = request.form['meta_instructions'].strip()
            user_query = request.form['user_query'].strip()

            # Handle uploaded files
            uploaded_files = request.files.getlist('uploaded_files')
            file_content = ""
            for file in uploaded_files:
                if file.filename:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    extracted_text = extract_text_from_file(filepath)
                    if "Error" in extracted_text:
                        error = f"Error processing file {file.filename}: {extracted_text}"
                    else:
                        file_content += extracted_text + "\n"

            # Store inputs
            inputs = {
                "Meta Instructions": meta_instructions,
                "User Query": user_query,
                "Uploaded Content": file_content.strip()
            }

            # Combine inputs into API prompt
            api_call_text = (
                f"{meta_instructions}\n\n"
                f"User Query: {user_query}\n\n"
                f"Uploaded Content:\n{file_content}"
            )

            # Call OpenAI API
            api_response = await call_openai_api(api_call_text)

        except Exception as e:
            error = f"An error occurred: {str(e)}"

    return render_template('index.html', inputs=inputs, api_call_text=api_call_text,
                           api_response=api_response, error=error, app_version=APP_VERSION)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
