from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json

app = Flask(__name__)
APP_VERSION = "0.1.15"

ICON_CONFIG_FILE = "icon_config.json"

def load_icon_config():
    """Load icon configuration from a JSON file."""
    try:
        with open(ICON_CONFIG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Create a default configuration if the file is missing or malformed
        default_config = {
            "App 1": "amber-button.jpeg",
            "App 2": "dewar-flask.jpeg",
            "App 3": "red-button.jpeg",
        }
        with open(ICON_CONFIG_FILE, "w") as f:
            json.dump(default_config, f)
        return default_config

def save_icon_config(config):
    """Save the icon configuration to a JSON file."""
    with open(ICON_CONFIG_FILE, "w") as f:
        json.dump(config, f)

@app.route('/')
def home():
    """Redirect to the gallery page."""
    return redirect(url_for('gallery'))

@app.route('/gallery', methods=["GET", "POST"])
def gallery():
    """Display the application gallery."""
    icon_config = load_icon_config()
    if request.method == "POST":
        # Update icon configuration if changes are submitted
        app_name = request.form.get("app_name")
        selected_icon = request.form.get("icon")
        if app_name and selected_icon:
            icon_config[app_name] = selected_icon
            save_icon_config(icon_config)
        return redirect(url_for('gallery'))

    return render_template('gallery.html', icon_config=icon_config, app_version=APP_VERSION)

@app.route('/angel-investment-analysis', methods=["GET", "POST"])
def angel_investment_analysis():
    """Render the Angel Investment Analysis page."""
    if request.method == "POST":
        meta_instructions = request.form.get("meta_instructions", "")
        user_query = request.form.get("user_query", "")
        uploaded_file = request.files.get("file_upload")
        if uploaded_file:
            file_path = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(file_path)
        else:
            file_path = None

        # Debugging message to track data flow
        print(f"Meta Instructions: {meta_instructions}")
        print(f"User Query: {user_query}")
        print(f"Uploaded File Path: {file_path}")

        # Mock API response for debugging
        api_response = f"Analyzing with meta instructions: {meta_instructions} and user query: {user_query}."

        return render_template(
            "angel_investment_analysis.html",
            meta_instructions=meta_instructions,
            user_query=user_query,
            api_response=api_response,
            file_path=file_path,
            app_version=APP_VERSION,
        )

    return render_template('angel_investment_analysis.html', app_version=APP_VERSION)

if __name__ == "__main__":
    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
