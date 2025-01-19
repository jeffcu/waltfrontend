import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify

# Flask application setup
app = Flask(__name__)

# Constants
APP_VERSION = "0.1.15"
ICON_CONFIG_PATH = "icon_config.json"

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Utility functions
def load_icon_config():
    """Load the icon configuration file. Create default config if invalid or missing."""
    try:
        with open(ICON_CONFIG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"Error loading icon_config.json: {e}. Initializing with default config.")
        default_config = {
            "Angel Investment Analysis": "dewar-flask.jpeg",
            "Coming Soon App 1": "placeholder.png",
            "Coming Soon App 2": "placeholder.png",
            "Coming Soon App 3": "placeholder.png",
        }
        with open(ICON_CONFIG_PATH, "w") as f:
            json.dump(default_config, f)
        return default_config

def save_icon_config(config):
    """Save the icon configuration to a file."""
    try:
        with open(ICON_CONFIG_PATH, "w") as f:
            json.dump(config, f)
        logging.info("Icon configuration saved successfully.")
    except Exception as e:
        logging.error(f"Error saving icon configuration: {e}")

# Routes
@app.route("/")
def home():
    """Redirect to gallery as the default view."""
    return redirect(url_for("gallery"))

@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    """Render the gallery page."""
    icon_config = load_icon_config()

    if request.method == "POST":
        # Update icon configuration based on user input
        app_name = request.form.get("app_name")
        icon_name = request.form.get("icon_name")
        if app_name and icon_name:
            icon_config[app_name] = icon_name
            save_icon_config(icon_config)
        return redirect(url_for("gallery"))

    return render_template("gallery.html", icons=icon_config, app_version=APP_VERSION)

@app.route("/angel-investment-analysis", methods=["GET", "POST"])
def angel_investment_analysis():
    """Render the Angel Investment Analysis application."""
    if request.method == "POST":
        meta_instructions = request.form.get("meta_instructions", "")
        user_query = request.form.get("user_query", "")
        file = request.files.get("file_upload")

        # Placeholder for analysis logic
        api_response = {
            "meta_instructions": meta_instructions,
            "user_query": user_query,
            "file_content": file.read().decode("utf-8") if file else "No file uploaded"
        }

        return render_template(
            "angel_investment_analysis.html",
            api_response=json.dumps(api_response, indent=4),
            app_version=APP_VERSION
        )

    return render_template("angel_investment_analysis.html", app_version=APP_VERSION)

# Main entry point
if __name__ == "__main__":
    if not os.path.exists(ICON_CONFIG_PATH):
        logging.info("Initializing icon_config.json with default values.")
        save_icon_config(load_icon_config())
    app.run(debug=True)
