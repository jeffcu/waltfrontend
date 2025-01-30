"""
Filename: virtual-lab.py
Location: Root directory of the Flask project.

Purpose:
- Main Flask application file.
- Handles routes for UI rendering, OpenAI API calls, and file uploads.
- Generates and formats PDF reports with structured numbering and spacing.
- Fixes WeasyPrint formatting issues and ensures proper Heroku compatibility.
"""

from flask import Flask, request, jsonify, render_template, send_file
import weasyprint
import os
from io import BytesIO
from PyPDF2 import PdfReader
import openai
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Home route redirecting to the gallery page
@app.route('/')
def home():
    return render_template('gallery.html')

# Route to render the angel investment analysis page
@app.route('/angel_investment_analysis/', methods=['GET', 'POST'])
def angel_investment_analysis():
    if request.method == 'POST':
        user_input = request.form.get('meta_instructions', '') + " " + request.form.get('user_query', '')
        file = request.files.get('file_upload')

        extracted_text = ""
        if file and file.filename != '':
            reader = PdfReader(file)
            extracted_text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
            user_input += " " + extracted_text

        if not user_input.strip():
            return render_template('angel_investment_analysis.html', analysis_result="No content provided")

        try:
            client = openai.Client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert on startup investment analysis."},
                    {"role": "user", "content": user_input}
                ]
            )
            analysis_result = format_response(response.choices[0].message.content.strip())
        except Exception as e:
            logging.error(f"API call failed: {str(e)}")
            analysis_result = f"API call failed: {str(e)}"

        return render_template('angel_investment_analysis.html', analysis_result=analysis_result)

    return render_template('angel_investment_analysis.html', analysis_result=None)

# Route for handling AJAX API call
@app.route('/analyze', methods=['POST'])
def analyze():
    user_input = request.form.get('meta_instructions', '') + " " + request.form.get('user_query', '')
    file = request.files.get('file_upload')

    extracted_text = ""
    if file and file.filename != '':
        reader = PdfReader(file)
        extracted_text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        user_input += " " + extracted_text

    if not user_input.strip():
        return jsonify({"Analysis Summary": "No content provided"})

    try:
        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert on startup investment analysis."},
                {"role": "user", "content": user_input}
            ]
        )
        analysis_result = format_response(response.choices[0].message.content.strip())
        logging.info(f"API Response: {analysis_result}")
    except Exception as e:
        logging.error(f"API call failed: {str(e)}")
        analysis_result = f"API call failed: {str(e)}"

    return jsonify({"Analysis Summary": analysis_result})

# Route to generate and download PDF report
@app.route('/download_report', methods=['POST'])
def download_report():
    """
    Generate a properly formatted PDF report.
    - Uses numbered sections (1., 2., 3.) with bold subtitles.
    - Sections are clearly separated for readability.
    """
    summary_data = request.form.get('summaryData')

    if not summary_data:
        logging.error("No summary data received for PDF generation.")
        return "No summary data provided", 400

    logging.info(f"Generating PDF with summary: {summary_data[:200]}...")

    formatted_summary = format_pdf_content(summary_data)

    html_content = f"""
    <html>
        <head>
            <title>Investment Report</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; padding: 20px; }}
                h1 {{ color: #2D9CDB; font-size: 24px; text-align: center; }}
                h2 {{ color: #27AE60; font-size: 18px; margin-bottom: 5px; }}
                .section {{ margin-bottom: 15px; }}
                .section-number {{ font-size: 18px; font-weight: bold; color: #333; }}
                .subtitle {{ font-size: 16px; font-weight: bold; color: #555; }}
                .content {{ font-size: 14px; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <h1>Angel Investment Analysis Report</h1>
            {formatted_summary}
        </body>
    </html>
    """

    pdf = weasyprint.HTML(string=html_content).write_pdf()
    pdf_stream = BytesIO(pdf)

    return send_file(
        pdf_stream,
        as_attachment=True,
        download_name="investment_report.pdf",
        mimetype='application/pdf'
    )

# Utility function for formatting API responses for web UI
def format_response(response_text):
    """
    Format API response for readability in the web UI.
    - Uses numbered sections (1., 2., 3.).
    - Each section has a subtitle, then a line break, then the content.
    """
    formatted_text = response_text.replace("**", "").replace("\n", "<br><br>")
    formatted_text = formatted_text.replace("1. ", "<strong>1. </strong>")
    formatted_text = formatted_text.replace("2. ", "<strong>2. </strong>")
    formatted_text = formatted_text.replace("3. ", "<strong>3. </strong>")
    formatted_text = formatted_text.replace("4. ", "<strong>4. </strong>")
    formatted_text = formatted_text.replace("5. ", "<strong>5. </strong>")

    return f"<strong>Analysis Report:</strong><br>{formatted_text}"

# Utility function for formatting PDF content properly
def format_pdf_content(summary_data):
    """
    Format content for structured PDF output.
    - Uses numbered sections (1., 2., 3.).
    - Ensures section numbers are followed by subtitles and content.
    - Sections are spaced out for readability.
    """
    formatted_text = summary_data.replace("**", "")
    formatted_text = formatted_text.replace("\n\n", "<br><br>")
    formatted_text = formatted_text.replace("1. ", "<div class='section'><span class='section-number'>1.</span> <span class='subtitle'>Introduction</span><br><div class='content'>")
    formatted_text = formatted_text.replace("2. ", "</div><div class='section'><span class='section-number'>2.</span> <span class='subtitle'>Market Analysis</span><br><div class='content'>")
    formatted_text = formatted_text.replace("3. ", "</div><div class='section'><span class='section-number'>3.</span> <span class='subtitle'>Financial Overview</span><br><div class='content'>")
    formatted_text = formatted_text.replace("4. ", "</div><div class='section'><span class='section-number'>4.</span> <span class='subtitle'>Competitive Landscape</span><br><div class='content'>")
    formatted_text = formatted_text.replace("5. ", "</div><div class='section'><span class='section-number'>5.</span> <span class='subtitle'>Conclusion</span><br><div class='content'>")

    return formatted_text + "</div>"

# Fix for Heroku: Bind to PORT
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
