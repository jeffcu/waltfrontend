# Filename: virtual-lab.py
# Location: virtual-lab.py (relative to root)
from flask import Flask, request, jsonify, render_template, send_file, abort
import os
import logging
import weasyprint
from io import BytesIO
from investment_analysis.services import InvestmentAnalysisService
from investment_analysis.utils import format_pdf_content # take out, not being used
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename  # for secure file uploads
from flask_wtf.csrf import CSRFProtect  # Import CSRFProtect
from walt.walt import walt_bp  # Import the walt blueprint

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Create an uploads folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key')  # Set a secret key for CSRF

# Create the uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Initialize InvestmentAnalysisService (pass API key)
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    logging.error("OPENAI_API_KEY not set in environment variables.")
    raise ValueError("OPENAI_API_KEY not set.  Please configure.")

analysis_service = InvestmentAnalysisService(openai_api_key=openai_api_key)


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
                                   analysis_result=f"An unexpected error occurred: {str(e)}")

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


# Error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=str(e)), 500

# Register the walt blueprint
app.register_blueprint(walt_bp)


# Fix for Heroku: Bind to PORT
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)  # Debug mode for development
