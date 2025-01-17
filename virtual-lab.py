import os
from flask import Flask, request, render_template
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from PyPDF2 import PdfReader

# Load the API key from .env file (for local testing)
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to store uploaded files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load predefined prompts from a file
PROMPTS_FILE = 'prompts.txt'
def load_prompts():
    """Load prompts and titles from the PROMPTS_FILE."""
    if os.path.exists(PROMPTS_FILE):
        prompts = []
        with open(PROMPTS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    title, prompt = line.split(',', 1)
                    prompts.append((title.strip(), prompt.strip()))
        return prompts
    return []

def save_prompts(prompts):
    """Save prompts and titles to the PROMPTS_FILE."""
    with open(PROMPTS_FILE, 'w') as f:
        for title, prompt in prompts:
            f.write(f"{title}, {prompt}\n")

PREDEFINED_PROMPTS = load_prompts()

# Initialize default prompts if the file is empty
if not PREDEFINED_PROMPTS:
    PREDEFINED_PROMPTS = [
        ("Summary", "Summarize the content: \n{content}"),
        ("Themes Analysis", "Analyze the key themes in the content: \n{content}"),
        ("Critical Evaluation", "Provide a critical evaluation: \n{content}"),
        ("Actionable Insights", "Extract actionable insights: \n{content}"),
        ("Challenges and Solutions", "Identify challenges and solutions: \n{content}"),
        ("Professional Response", "Compose a professional response: \n{content}")
    ]
    save_prompts(PREDEFINED_PROMPTS)

async def call_openai_api(prompt):
    """Asynchronous function to call OpenAI API with a prompt."""
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
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
            reader = PdfReader(filepath)
            return "\n".join([page.extract_text() for page in reader.pages])
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
    responses = []
    error = ""

    if request.method == 'POST':
        try:
            # Get user input
            user_query = request.form['user_query'].encode('utf-8', errors='replace').decode('utf-8')
            uploaded_files = request.files.getlist('uploaded_files')

            # Read content from uploaded files
            file_content = ""
            for file in uploaded_files:
                if file.filename:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    file_content += extract_text_from_file(filepath).encode('utf-8', errors='replace').decode('utf-8') + "\n"

            # Combine user query and file content
            combined_content = f"User Query: {user_query}\n\nUploaded Content:\n{file_content}"

            # Generate prompts and make API calls
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = [
                call_openai_api(prompt.format(content=combined_content)) for _, prompt in PREDEFINED_PROMPTS
            ]
            responses = loop.run_until_complete(asyncio.gather(*tasks))
            loop.close()

            # Format responses with titles
            responses = [
                {"title": title, "response": response}
                for (title, _), response in zip(PREDEFINED_PROMPTS, responses)
            ]

        except Exception as e:
            error = f"An error occurred: {str(e)}"

    return render_template('index.html', responses=responses if request.method == 'POST' else None, error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
