from flask import Flask, render_template, request, redirect, jsonify
import os
import json

app = Flask(__name__)

APP_VERSION = "0.2.1"
ICON_CONFIG_PATH = "static/icons/icon_config.json"

# Helper function to load icon configuration
def load_icon_config():
    if not os.path.exists(ICON_CONFIG_PATH):
        default_config = {
            "angel_investment_analysis": "amber-button.jpeg"
        }
        with open(ICON_CONFIG_PATH, "w") as f:
            json.dump(default_config, f)
    with open(ICON_CONFIG_PATH, "r") as f:
        return json.load(f)

# Route for the gallery
@app.route("/gallery")
def gallery():
    icon_config = load_icon_config()
    return render_template("gallery.html", icon_config=icon_config, app_version=APP_VERSION)

# Route for the Angel Investment Analysis app
@app.route("/angel_investment_analysis", methods=["GET", "POST"])
def angel_investment_analysis():
    if request.method == "POST":
        meta_instructions = request.form.get("meta_instructions", "")
        user_query = request.form.get("user_query", "")
        # Process uploaded files and analysis logic here
        return render_template(
            "angel_investment_analysis.html",
            meta_instructions=meta_instructions,
            user_query=user_query,
            api_response=None,  # Placeholder for actual API response
            app_version=APP_VERSION,
        )
    return render_template("angel_investment_analysis.html", app_version=APP_VERSION)

# Handle static icons for selection
@app.route("/update-icon", methods=["POST"])
def update_icon():
    data = request.json
    app_name = data.get("app_name")
    icon_name = data.get("icon_name")
    icon_config = load_icon_config()
    icon_config[app_name] = icon_name
    with open(ICON_CONFIG_PATH, "w") as f:
        json.dump(icon_config, f)
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)
