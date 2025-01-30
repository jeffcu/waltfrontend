"""
Filename: virtual-lab.py
Location: Root directory of the Flask project.

Purpose:
- Main Flask application file.
- Handles routes for UI rendering, OpenAI API calls, and file uploads.
- Generates and formats PDF reports with proper numbering and spacing.
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
        analysis_result = format_response(response.choices[0].message.content.strip())
        logging.info(f"API Response: {analysis_result}")
    except Exception as e:
        logging.error(f"API call failed: {str(e)}")
        analysis_result = f"API call failed: {str(e)}"

    return jsonify({"Analysis Summary": analysis_result})

# Route for the API test functionality
@app.route('/api_test', methods=['POST'])
def api_test():
    """
    Handles OpenAI API requests for the API Test popup.
    """
    data = request.json
    user_query = data.get('query', 'Who invented velcro?')

    if not user_query.strip():
        return jsonify({"response": "Error: Query is empty"}), 400

    try:
        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an API testing assistant."},
                {"role": "user", "content": user_query}
            ]
        )
        api_response = format_response(response.choices[0].message.content.strip())
        return jsonify({"response": api_response})
    except Exception as e:
        logging.error(f"OpenAI API call failed: {str(e)}")
        return jsonify({"response": f"Error: {str
