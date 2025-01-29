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
            analysis_result = response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"API call failed: {str(e)}")
            analysis_result = f"API call failed: {str(e)}"

        return render_template('angel_investment_analysis.html', analysis_result=analysis_result)

    return render_template('angel_investment_analysis.html', analysis_result=None)

# Route to handle AJAX API call for analysis
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
        analysis_result = response.choices[0].message.content.strip()
        logging.info(f"API Response: {analysis_result}")
    except Exception as e:
        logging.error(f"API call failed: {str(e)}")
        analysis_result = f"API call failed: {str(e)}"

    return jsonify({"Analysis Summary": analysis_result})

# Route to generate and download PDF report
@app.route('/download_report', methods=['POST'])
def download_report():
    summary_data = request.form.get('summaryData')

    if not summary_data:
        return "No summary data provided", 400

    # Generate PDF using WeasyPrint
    html_content = f"""
    <html>
        <head><title>Investment Report</title></head>
        <body>
            <h1>Angel Investment Analysis Report</h1>
            <div>{summary_data}</div>
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

# File upload processing
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file_upload' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file_upload']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    return jsonify({"success": f"File {file.filename} uploaded successfully"})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
