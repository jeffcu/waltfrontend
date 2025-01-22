from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import json
import os
import openai
from weasyprint import HTML

app = Flask(__name__)

# Ensure the icon configuration file exists
ICON_CONFIG_FILE = "icon-config.json"

default_icon_config = {
    "Angel Investment Analysis": "amber-button.jpeg"
}

def load_icon_config():
    if not os.path.exists(ICON_CONFIG_FILE):
        save_icon_config(default_icon_config)
    with open(ICON_CONFIG_FILE, "r") as f:
        return json.load(f)

def save_icon_config(config):
    with open(ICON_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('gallery'))

@app.route('/gallery')
def gallery():
    icon_config = load_icon_config()
    return render_template('gallery.html', icon_config=icon_config)

@app.route('/update_icon', methods=['POST'])
def update_icon():
    app_name = request.form.get('app_name')
    icon_file = request.form.get('icon_file')
    icon_config = load_icon_config()
    icon_config[app_name] = icon_file
    save_icon_config(icon_config)
    return redirect(url_for('gallery'))

@app.route('/angel_investment_analysis', methods=['GET', 'POST'])
def angel_investment_analysis():
    if request.method == 'POST':
        meta_instructions = request.form.get('meta_instructions')
        user_query = request.form.get('user_query')
        uploaded_file = request.files.get('file_upload')

        # Read the uploaded file safely
        file_content = ""
        if uploaded_file and uploaded_file.filename != '':
            try:
                file_content = uploaded_file.read().decode("utf-8")
            except UnicodeDecodeError:
                try:
                    file_content = uploaded_file.read().decode("ISO-8859-1")
                except Exception as e:
                    file_content = "Error reading file content."

        # Prepare input for OpenAI API
        input_text = f"{meta_instructions}\n\nUser Query: {user_query}\n\nFile Content:\n{file_content}"

        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": meta_instructions},
                    {"role": "user", "content": user_query + "\n\n" + file_content}
                ],
                max_tokens=500,
                temperature=0.7
            )

            analysis_result = response.choices[0].message['content']
        except Exception as e:
            analysis_result = f"Error: {str(e)}"

        return render_template('index.html',
                               meta_instructions=meta_instructions,
                               user_query=user_query,
                               analysis_result=analysis_result)

    return render_template('index.html')

@app.route('/download_report')
def download_report():
    analysis_result = request.args.get('analysis_result', 'No analysis available')

    # Create a PDF report
    report_html = f"""
    <html>
    <head>
        <title>Investment Analysis Report</title>
    </head>
    <body>
        <h1>Investment Analysis Report</h1>
        <p>{analysis_result}</p>
    </body>
    </html>
    """

    pdf_file_path = "static/output_report.pdf"
    HTML(string=report_html).write_pdf(pdf_file_path)

    return send_file(pdf_file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
