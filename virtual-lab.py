import os
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Version for the application
APP_VERSION = "0.1.1"

# Icon configuration file
ICON_CONFIG_FILE = "icon_config.json"

def save_icon_config(config):
    """Saves the icon configuration to a JSON file."""
    with open(ICON_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def load_icon_config():
    """
    Loads the icon configuration from the JSON file.
    If the file does not exist or is invalid, it creates one with default values.
    """
    if not os.path.exists(ICON_CONFIG_FILE):
        print("Icon configuration file not found. Creating a new one with default values.")
        initial_config = {
            "Angel Investment Analysis": "dewar-flask.jpeg",
            "Coming Soon App 1": "dewar-flask.jpeg",
            "Coming Soon App 2": "dewar-flask.jpeg"
        }
        save_icon_config(initial_config)
        return initial_config

    try:
        with open(ICON_CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        print("Invalid JSON in icon configuration file. Recreating with default values.")
        initial_config = {
            "Angel Investment Analysis": "dewar-flask.jpeg",
            "Coming Soon App 1": "dewar-flask.jpeg",
            "Coming Soon App 2": "dewar-flask.jpeg"
        }
        save_icon_config(initial_config)
        return initial_config

@app.route('/gallery', methods=["GET", "POST"])
def gallery():
    """Handles the gallery page and allows updating app icons."""
    icon_config = load_icon_config()
    available_icons = os.listdir("static/icons")  # Load available icons from the icons directory

    if request.method == "POST":
        app_name = request.form.get("app_name")
        selected_icon = request.form.get("icon_select")
        if app_name and selected_icon:
            icon_config[app_name] = selected_icon
            save_icon_config(icon_config)  # Save updated configuration
            print(f"Updated {app_name} to use {selected_icon}")

    return render_template(
        "gallery.html",
        app_version=APP_VERSION,
        available_icons=available_icons,
        icon_config=icon_config
    )

@app.route('/angel-investment-analysis', methods=["GET", "POST"])
def angel_investment_analysis():
    """Handles the Angel Investment Analysis application."""
    if request.method == "POST":
        # Process inputs and generate results
        meta_instructions = request.form.get("meta_instructions", "")
        user_query = request.form.get("user_query", "")
        uploaded_file = request.files.get("file_upload")

        # Debugging: Log inputs
        print("Meta Instructions:", meta_instructions)
        print("User Query:", user_query)
        print("Uploaded File:", uploaded_file.filename if uploaded_file else "No file uploaded")

        # Example result processing (replace with your API call)
        results = f"Meta: {meta_instructions}\nQuery: {user_query}\nFile: {uploaded_file.filename if uploaded_file else 'No file provided'}"

        return render_template(
            "angel_investment_analysis.html",
            app_version=APP_VERSION,
            results=results
        )

    return render_template("angel_investment_analysis.html", app_version=APP_VERSION)

@app.route('/')
def home():
    """Redirect to the gallery."""
    return redirect(url_for('gallery'))

if __name__ == "__main__":
    # Ensure the static/icons directory exists
    if not os.path.exists("static/icons"):
        os.makedirs("static/icons")
        print("Created static/icons directory.")

    # Ensure the icon config is initialized
    config = load_icon_config()
    print(f"Loaded icon configuration: {config}")

    # Run the Flask app
    app.run(debug=True)
