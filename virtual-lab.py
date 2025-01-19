from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json

app = Flask(__name__)

# App version
APP_VERSION = "0.1.15"

# Paths
ICON_CONFIG_PATH = "icon_config.json"
STATIC_ICON_PATH = "static/icons/"

# Ensure icon_config.json exists with default values
def initialize_icon_config():
    if not os.path.exists(ICON_CONFIG_PATH):
        default_config = {
            "Angel Investment Analysis": "dewar-flask.jpeg",
            "Coming Soon App 1": "placeholder.png",
            "Coming Soon App 2": "placeholder.png",
            "Coming Soon App 3": "placeholder.png",
        }
        with open(ICON_CONFIG_PATH, "w") as f:
            json.dump(default_config, f)

# Load icon configuration
def load_icon_config():
    with open(ICON_CONFIG_PATH, "r") as f:
        return json.load(f)

# Save icon configuration
def save_icon_config(config):
    with open(ICON_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

@app.route('/')
def home():
    """Redirect to the gallery as the main page."""
    return redirect(url_for('gallery'))

@app.route('/gallery')
def gallery():
    """Render the application gallery page."""
    initialize_icon_config()
    icon_config = load_icon_config()
    return render_template("gallery.html", icon_config=icon_config, app_version=APP_VERSION)

@app.route('/angel-investment-analysis', methods=['GET', 'POST'])
def angel_investment_analysis():
    """Render and handle Angel Investment Analysis application."""
    if request.method == 'POST':
        meta_instructions = request.form.get("meta_instructions", "")
        user_query = request.form.get("user_query", "")
        uploaded_file = request.files.get("file_upload")

        file_content = ""
        if uploaded_file and uploaded_file.filename != "":
            file_path = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

        # Placeholder: Simulate API call
        api_response = {
            "summary": f"Meta Instructions: {meta_instructions}\nUser Query: {user_query}\nFile Content: {file_content}"
        }

        return render_template(
            "angel-investment-analysis.html",
            api_response=api_response,
            app_version=APP_VERSION
        )

    return render_template("angel-investment-analysis.html", app_version=APP_VERSION)

@app.route('/update-icon', methods=['POST'])
def update_icon():
    """Updates the icon for a specific application."""
    data = request.get_json()
    app_name = data.get("app_name")
    new_icon = data.get("icon")

    if app_name and new_icon:
        icon_config = load_icon_config()
        if app_name in icon_config:
            icon_config[app_name] = new_icon
            save_icon_config(icon_config)
            return jsonify({"status": "success", "message": "Icon updated."}), 200
        return jsonify({"status": "error", "message": "App not found."}), 400

    return jsonify({"status": "error", "message": "Invalid request."}), 400

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Initialize icon config
initialize_icon_config()

if __name__ == "__main__":
    app.run(debug=True)
