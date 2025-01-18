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
APP_VERSION = "0.0.8"

# Load predefined prompts from a file
PROMPTS_FILE = 'prompts.txt'
def load_prompts():
    """Load prompts and titles from the PROMPTS_FILE."""
    prompts = []
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if ',' in line:
                    title, prompt = line.split(',', 1)
                    prompts.append((title.strip(), prompt.strip()))
                else:
                    print(f"Skipping invalid line in prompts file: {line}")
    return prompts

def save_prompts(prompts):
    """Save prompts to the PROMPTS_FILE."""
    with open(PROMPTS_FILE, 'w') as f:
        for title, prompt in prompts:
            f.write(f"{title}, {prompt}\n")

PREDEFINED_PROMPTS = load_prompts()

# Remove duplicate entries by title
unique_prompts = {}
for title, prompt in PREDEFINED_PROMPTS:
    unique_prompts[title] = prompt
PREDEFINED_PROMPTS = list(unique_prompts.items())

# Save the updated prompts back to the file
save_prompts(PREDEFINED_PROMPTS)

async def call_openai_api(prompt):
    """Asynchronous function to call OpenAI API with a prompt."""
    try:
        return prompt  # Return the input prompt instead of making an API call
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
    """Renders the main page with the user query input and displays the responses."""
    responses = None
    error = ""
    user_query = ""
    uploaded_files_content = ""
    status_messages = []
    meta_instructions = (
        "You are an expert AI specializing in detailed analysis. Generate responses in markdown format "
        "with bullet points, focusing on specific companies, markets, and actionable insights."
    )  # Default meta instructions

    if request.method == 'POST':
        try:
            user_query = request.form['user_query'].encode('utf-8', errors='replace').decode('utf-8').strip()
            meta_instructions = request.form['meta_instructions'].strip()
            if not user_query:
                raise ValueError("No user query provided.")
            status_messages.append("User query and meta-instructions received.")

            uploaded_files = request.files.getlist('uploaded_files')
            file_content = ""
            word_count = 0
            for file in uploaded_files:
                if file.filename:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    extracted_text = extract_text_from_file(filepath)
                    if "Error" in extracted_text:
                        status_messages.append(f"Error processing file {file.filename}: {extracted_text}")
                    else:
                        word_count += len(extracted_text.split())
                        file_content += extracted_text + "\n"
            if word_count > 0:
                status_messages.append(f"Successfully extracted {word_count} words from uploaded files.")
            else:
                raise ValueError("No valid content extracted from uploaded files.")

            if not PREDEFINED_PROMPTS:
                raise ValueError("No prompts are defined for API calls.")

            # Debug logs for inputs
            print(f"Debug: Meta Instructions:\n{meta_instructions}")
            print(f"Debug: User Query:\n{user_query}")
            print(f"Debug: File Content:\n{file_content}")

            combined_content = [
                {
                    "title": title,
                    "full_prompt": prompt.format(content=f"{meta_instructions}\n\nUser Query: {user_query}\n\nUploaded Content:\n{file_content}")
                }
                for title, prompt in PREDEFINED_PROMPTS
            ]

            # Debug logs for combined content
            for item in combined_content:
                print(f"Debug: Combined Content for {item['title']}\n{item['full_prompt']}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = [
                call_openai_api(item["full_prompt"]) for item in combined_content
            ]
            status_messages.append("Generating API input preview for all prompts.")
            results = loop.run_until_complete(asyncio.gather(*tasks))
            loop.close()

            responses = [
                {"title": item["title"], "response": result}
                for item, result in zip(combined_content, results)
            ]
            status_messages.append("Input previews generated successfully.")

        except ValueError as ve:
            error = str(ve)
        except Exception as e:
            error = f"An error occurred: {str(e)}"

    return render_template('index.html', responses=responses, error=error, user_query=user_query,
                           meta_instructions=meta_instructions, uploaded_files_content=uploaded_files_content,
                           status_messages=status_messages, app_version=APP_VERSION)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
