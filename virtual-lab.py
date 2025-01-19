import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

APP_VERSION = "0.1.15"
ICON_CONFIG_PATH = "icon_config.json"
STATIC_ICONS_PATH = "static/icons"


def load_icon_config():
    """Load the icon configuration file. Create a default if it doesn't exist."""
    if not os.path.exists(ICON_CONFIG_PATH):
        default_config = {
            "Angel Investment Analysis": "amber-button.jpeg",
            "Coming Soon 1": "amber-button.jpeg",
            "Coming Soon 2": "amber-button.jpeg",
            "Coming Soon 3": "amber-button.jpeg"
        }
        with open(ICON_CONFIG_PATH, "w") as f:
            json.dump(default_config, f)
        return default_config
    else:
        with open(ICON_CONFIG_PATH, "r") as f:
            return json.load(f)


def save_icon_config(config):
    """Save the icon configuration to the JSON file."""
    with open(ICON_CONFIG_PATH, "w") as f:
        json.dump(config, f)


@app.route("/")
def home():
    """Redirect to gallery by default."""
    return redirect(url_for("gallery"))


@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    """Render the gallery with available applications."""
    try:
        icon_config = load_icon_config()
    except Exception as e:
        return f"Error loading icon configuration: {e}"

    if request.method == "POST":
        app_name = request.form.get("app_name")
        new_icon = request.form.get("icon")
        if app_name and new_icon:
            icon_config[app_name] = new_icon
            save_icon_config(icon_config)
            return redirect(url_for("gallery"))

    available_icons = [
        f for f in os.listdir(STATIC_ICONS_PATH) if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    return render_template(
        "gallery.html",
        app_version=APP_VERSION,
        icon_config=icon_config,
        available_icons=available_icons
    )


@app.route("/angel-investment-analysis", methods=["GET", "POST"])
def angel_investment_analysis():
    """Handle Angel Investment Analysis application."""
    if request.method == "POST":
        meta_instructions = request.form.get("meta_instructions", "")
        user_query = request.form.get("user_query", "")
        file = request.files.get("file_upload")

        # For debugging: check inputs
        print(f"Meta Instructions: {meta_instructions}")
        print(f"User Query: {user_query}")

        # Save uploaded file (if any)
        uploaded_file_path = None
        if file:
            uploaded_file_path = os.path.join("uploads", file.filename)
            file.save(uploaded_file_path)

        # Simulate API response
        api_response = {
            "company_name": "Example Startup, Inc.",
            "market": "AI and Machine Learning",
            "strengths": ["Innovative product", "Strong team", "Large market potential"],
            "weaknesses": ["High competition", "Unproven revenue model", "Scalability concerns"]
        }

        return render_template(
            "angel_investment_analysis.html",
            app_version=APP_VERSION,
            meta_instructions=meta_instructions,
            user_query=user_query,
            api_response=api_response,
            uploaded_file_path=uploaded_file_path
        )
    return render_template(
        "angel_investment_analysis.html",
        app_version=APP_VERSION
    )


@app.route("/icon-preview/<icon_name>")
def icon_preview(icon_name):
    """Endpoint to serve icon previews."""
    icon_path = os.path.join(STATIC_ICONS_PATH, icon_name)
    if os.path.exists(icon_path):
        return jsonify({"icon_url": url_for("static", filename=f"icons/{icon_name}")})
    else:
        return jsonify({"error": "Icon not found"}), 404


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
