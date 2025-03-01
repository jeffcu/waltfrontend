import os
from flask import Flask, request, render_template, send_file, jsonify
from dotenv import load_dotenv
import numpy as np
import json
import logging
import weasyprint
from io import BytesIO
from investment_analysis.services import InvestmentAnalysisService
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect, generate_csrf
from walt.walt import walt_bp
from walt2.walt2 import walt2_bp # Import the new walt2 blueprint
from waltx.waltx import waltx_bp # Import the new waltx blueprint  <-- ADDED
from flask_session import Session # Import Flask-Session
import colorsys #Import colorsys
import random

# Import Word Counter blueprint
from word_counter.word_counter import wc_bp

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to store uploaded files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key')  # Set a secret key for CSRF

# Configure Flask-Session (for storing conversation history)
app.config['SESSION_TYPE'] = 'filesystem'  # Or 'redis', 'mongodb', etc.
app.config['SESSION_PERMANENT'] = False  # Session expires when browser closes
app.config['SESSION_KEY_PREFIX'] = 'walt_'  # Prevents conflicts with other session data
Session(app) # Initialize Flask-Session

# Initialize CSRF protection  <-- ADDED - IMPORTANT
csrf = CSRFProtect(app)  # Initialize CSRF protection with the app  <-- CHANGED

# Inject CSRF token into all templates  <-- ADDED - IMPORTANT
@app.after_request
def inject_csrf_token(response):
    response.set_cookie('csrf_token', generate_csrf())  # Set a cookie to access the token
    return response

# Initialize InvestmentAnalysisService (pass API key)
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    logging.error("OPENAI_API_KEY not set in environment variables.")
    raise ValueError("OPENAI_API_KEY not set.  Please configure.")

analysis_service = InvestmentAnalysisService(openai_api_key=openai_api_key)

# Application version
APP_VERSION = "0.1.17"  #increment for change

# Define color palettes
COLOR_PALETTES = [
    ["#33FF33", "#FF3333", "#3333FF"],  # Green, Red, Blue
    ["#FFFF33", "#33FFFF", "#FF33FF"],  # Yellow, Cyan, Magenta
    ["#FF8000", "#8000FF", "#00FF80"],  # Orange, Violet, Spring Green
    ["#808080", "#C0C0C0", "#FFFFFF"]   # Gray, Silver, White
]

# Initialize the palette index
palette_index = 0


@app.route('/dynamic')
def dynamic():
    return render_template('dynamic.html')


@app.route('/dynamic_data')
def dynamic_data():
    global palette_index
    # Option 1: Sine Wave Graph
    num_points = 640
    x = np.linspace(0, 10 * np.pi, num_points)
    y = np.sin(x)
    sine_data = {'x': x.tolist(), 'y': y.tolist()}
    # Option 2: Mandelbrot Set
    width, height, max_iter = 640, 640, 50  # Increased resolution
    mandelbrot_set = calculate_mandelbrot(width, height, max_iter, palette_index)
    mandelbrot_data = mandelbrot_set.tolist()
    palette_index = (palette_index + 1) % len(COLOR_PALETTES)  # Increment and loop

    return jsonify({'mandelbrot': mandelbrot_data, 'sine': sine_data})


# Mandelbrot Set Calculator Function
def calculate_mandelbrot(width, height, max_iter, palette_index):
    x_min, x_max = -2.0, 1.0
    y_min, y_max = -1.5, 1.5

    image = np.zeros((height, width, 3), dtype=np.uint8)  # 3 channels for RGB color
    palette = COLOR_PALETTES[palette_index]

    x_range = np.linspace(x_min, x_max, width)
    y_range = np.linspace(y_min, y_max, height)

    for i in range(height):
        for j in range(width):
            c = complex(x_range[j], y_range[i])
            z = 0
            for k in range(max_iter):
                z = z * z + c
                if abs(z) > 2:
                    # Colorization based on iteration count:
                    color = palette[k % len(palette)]  # Select color from palette

                    # Convert hex to RGB
                    color = color.lstrip('#')
                    r, g, b = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                    image[i, j] = [r, g, b]
                    break
            else:
                image[i, j] = [0, 0, 0]  # Black if it belongs to the set

    return image

# Home route redirecting to the gallery page
@app.route('/')
def home():
    return render_template('gallery.html')


ALLOWED_EXTENSIONS = {'pdf'}  # only allow pdf files


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        extracted_text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return extracted_text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        raise ValueError("Error extracting text from PDF.  Ensure it's a valid PDF.") from e


# Route to render the angel investment analysis page
@app.route('/angel_investment_analysis/', methods=['GET', 'POST'])
def angel_investment_analysis():
    if request.method == 'POST':
        try:
            user_input = request.form.get('meta_instructions', '') + " " + request.form.get('user_query', '')
            file = request.files.get('file_upload')

            if file and file.filename != '':
                if not allowed_file(file.filename):
                    return render_template('angel_investment_analysis.html',
                                           analysis_result="Invalid file type. Only PDF files are allowed.")

                extracted_text = extract_text_from_pdf(file)
                user_input += " " + extracted_text

            if not user_input.strip():
                return render_template('angel_investment_analysis.html', analysis_result="No content provided")

            analysis_result = analysis_service.analyze_investment(user_input)

            return render_template('angel_investment_analysis.html', analysis_result=analysis_result)

        except ValueError as e:
            logging.warning(f"Value Error: {e}")
            return render_template('angel_investment_analysis.html', analysis_result=str(e))
        except Exception as e:
            logging.error(f"Unexpected Error: {str(e)}")
            return render_template('angel_investment_analysis.html',
                                   analysis_result=f"An unexpected error occurred: {str(e)}.")

    return render_template('angel_investment_analysis.html', analysis_result=None)


# Route for handling AJAX API call
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        user_input = request.form.get('meta_instructions', '') + " " + request.form.get('user_query', '')
        file = request.files.get('file_upload')

        if file and file.filename != '':
            if not allowed_file(file.filename):
                return jsonify({"Analysis Summary": "Invalid file type. Only PDF files are allowed."})

            extracted_text = extract_text_from_pdf(file)
            user_input += " " + extracted_text

        if not user_input.strip():
            return jsonify({"Analysis Summary": "No content provided"})

        analysis_result = analysis_service.analyze_investment(user_input)
        logging.info(f"API Response: {analysis_result}")
        return jsonify({"Analysis Summary": analysis_result})

    except ValueError as e:
        logging.warning(f"Value Error: {e}")
        return jsonify({"Analysis Summary": str(e)})

    except Exception as e:
        logging.error(f"Unexpected Error: {str(e)}")
        return jsonify({"Analysis Summary": f"An unexpected error occurred: {str(e)}"})


# Route to generate and download PDF report
@app.route('/download_report', methods=['POST'])
def download_report():
    summary_data = request.form.get('summaryData')

    if not summary_data:
        logging.error("No summary data received for PDF generation.")
        abort(400, description="No summary data provided")

    logging.info(f"Generating PDF with summary: {summary_data[:200]}...")

    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Angel Investment Analysis Summary</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; padding: 20px; }}
                h1 {{ color: #2D9CDB; font-size: 24px; text-align: center; }}
                pre {{ white-space: pre-wrap; word-break: break-word; font-family: 'Arial', sans-serif; }} /* Use pre tag to preserve formatting */
            </style>
        </head>
        <body>
            <h1>Angel Investment Analysis Summary</h1>
            <pre>{summary_data}</pre>  <!-- Display the raw summary data -->
        </body>
    </html>
    """

    try:
        pdf = BytesIO(weasyprint.HTML(string=html_content).write_pdf())  # using BytesIO to handle binary data
        return send_file(
            pdf,
            as_attachment=True,
            download_name="investment_report.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        logging.error(f"PDF generation failed: {str(e)}")
        abort(500, description=f"PDF generation failed: {str(e)}")


# New route to serve static API testing window
@app.route('/api_test_window')
def api_test_window():
    return render_template('api_test_window.html')

# New route to display images from /static/images/jeffsart
@app.route('/jeffsart/<filename>')
def jeffsart_image(filename):
    image_path = os.path.join('images', 'jeffsart', filename) # Corrected line
    full_path = os.path.join('static', image_path)
    logging.info(f"Image path: {image_path}")  # Log the relative path
    logging.info(f"Full path: {full_path}")  # Log the absolute path
    if os.path.isfile(full_path):
        return render_template('jeffsart_image.html', image_path=image_path)
    else:
        abort(404)

# Register the walt blueprint
app.register_blueprint(walt_bp, url_prefix='/walt')

# Register the walt2 blueprint (new Walt2)  <-- ADDED
app.register_blueprint(walt2_bp, url_prefix='/walt2')

# Register the waltx blueprint (new WaltX)  <-- ADDED
app.register_blueprint(waltx_bp, url_prefix='/waltx')

# Register the Word Counter blueprint  <-- ADDED
app.register_blueprint(wc_bp)

# Fix for Heroku: Bind to PORT
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
