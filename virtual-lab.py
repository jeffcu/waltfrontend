from flask import Flask, request, jsonify, render_template, send_file
import weasyprint
import os
from io import BytesIO

app = Flask(__name__)

# Home route redirecting to the gallery page
@app.route('/')
def home():
    return render_template('gallery.html')

# Route to render the angel investment analysis page
@app.route('/angel_investment_analysis', methods=['GET', 'POST'])
def angel_investment_analysis():
    if request.method == 'POST':
        user_input = request.form.get('meta_instructions')
        if not user_input:
            return render_template('angel_investment_analysis.html', analysis_result="No input provided")

        # Simulated analysis logic
        analysis_result = f"Analysis for input: {user_input}"

        return render_template('angel_investment_analysis.html', analysis_result=analysis_result)

    return render_template('angel_investment_analysis.html', analysis_result=None)

# Route to handle AJAX API call for analysis
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    user_input = data.get('userInput')

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # Simulated response for the provided input
    analysis_result = {
        "Company Name": f"Analyzed {user_input}",
        "Market Analysis": "Strong market presence with high growth potential.",
        "Risk Factors": "Medium risk due to competition.",
        "Recommendation": "Consider further due diligence before investing."
    }

    return jsonify(analysis_result)

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
