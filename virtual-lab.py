import os
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Path to icon configuration JSON
ICON_CONFIG_PATH = "static/icons/icon_config.json"

def load_icon_config():
    """Load icon configuration from the JSON file."""
    if not os.path.exists(ICON_CONFIG_PATH):
        default_config = {
            "Angel Investment Analysis": "dewar-flask.jpeg"
        }
        with open(ICON_CONFIG_PATH, "w") as f:
            json.dump(default_config, f)
        return default_config
    with open(ICON_CONFIG_PATH, "r") as f:
        return json.load(f)

def save_icon_config(icon_config):
    """Save updated icon configuration to the JSON file."""
    with open(ICON_CONFIG_PATH, "w") as f:
        json.dump(icon_config, f)

@app.route("/")
def gallery():
    """Display the gallery of applications."""
    icon_config = load_icon_config()
    return render_template("gallery.html", icon_config=icon_config)

@app.route("/set-icon/<app_name>", methods=["POST"])
def set_icon(app_name):
    """Set a new icon for a given application."""
    icon_config = load_icon_config()
    new_icon = request.form.get("icon_select")
    if app_name in icon_config and new_icon:
        icon_config[app_name] = new_icon
        save_icon_config(icon_config)
    return redirect(url_for("gallery"))

@app.route("/angel-investment-analysis", methods=["GET", "POST"])
def angel_investment_analysis():
    """Handle the Angel Investment Analysis application."""
    if request.method == "POST":
        meta_instructions = request.form.get("meta_instructions", "")
        user_query = request.form.get("user_query", "")
        uploaded_file = request.files.get("file_upload", None)

        # Placeholder for processing logic
        api_response = "Simulated API response based on input data."

        return render_template(
            "angel_investment_analysis.html",
            api_response=api_response,
            meta_instructions=meta_instructions,
            user_query=user_query,
        )
    return render_template("angel_investment_analysis.html", api_response=None)

if __name__ == "__main__":
    app.run(debug=True)
