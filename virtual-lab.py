from flask import Flask, render_template, request, jsonify, send_file
import os
import json

# Initialize the Flask app
app = Flask(__name__)

# Application version
APP_VERSION = "0.1.15"

# Directory for static icons
ICON_DIR = "static/icons"

# Function to load icons dynamically
def load_icons():
    return [icon for icon in os.listdir(ICON_DIR) if icon.endswith(('.png', '.jpg', '.jpeg'))]

# Route for the gallery
@app.route('/gallery')
def gallery():
    return render_template("gallery.html", app_version=APP_VERSION)

# Route for Angel Investment Analysis
@app.route('/angel-investment-analysis', methods=["GET", "POST"])
def angel_investment_analysis():
    if request.method == "POST":
        # Collect inputs
        meta_instructions = request.form.get("meta_instructions")
        user_query = request.form.get("user_query")
        selected_icon = request.form.get("icon_select")

        # Handle file upload
        uploaded_file = request.files.get("file_upload")
        if uploaded_file:
            file_path = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(file_path)
        else:
            file_path = None

        # Debugging: Display inputs
        print(f"Meta Instructions: {meta_instructions}")
        print(f"User Query: {user_query}")
        print(f"Selected Icon: {selected_icon}")
        print(f"Uploaded File Path: {file_path}")

        # Placeholder API response logic
        api_response = f"Simulated API response for query: {user_query}"

        # Render the template with results
        return render_template(
            "index.html",
            app_version=APP_VERSION,
            api_response=api_response,
            available_icons=load_icons(),
            selected_icon=selected_icon,
            error=None
        )
    else:
        # Render the initial page with icons
        return render_template(
            "index.html",
            app_version=APP_VERSION,
            available_icons=load_icons()
        )

# Route for downloading the report
@app.route('/download', methods=["POST"])
def download():
    # Simulated report content
    report_content = "Generated PDF content goes here."
    report_path = "uploads/report.pdf"

    # Write the report to a file
    with open(report_path, "w") as report_file:
        report_file.write(report_content)

    # Return the generated file to the user
    return send_file(report_path, as_attachment=True)

# Ensure directories exist for uploads and icons
if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs(ICON_DIR, exist_ok=True)

    # Run the application
    app.run(debug=True)
