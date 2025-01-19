from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json

# Initialize Flask app
app = Flask(__name__)

# Application version
APP_VERSION = "0.1.17"

# Directory for icons
ICON_DIR = "static/icons"

# File to store icon selections
ICON_CONFIG_FILE = "icon_config.json"

# Load or initialize icon configuration
def load_icon_config():
    if os.path.exists(ICON_CONFIG_FILE):
        with open(ICON_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_icon_config(config):
    with open(ICON_CONFIG_FILE, "w") as f:
        json.dump(config, f)

# Ensure directories exist
os.makedirs(ICON_DIR, exist_ok=True)

# Load available icons
def load_icons():
    return [icon for icon in os.listdir(ICON_DIR) if icon.endswith(('.png', '.jpg', '.jpeg'))]

# Root route
@app.route('/')
def home():
    return redirect('/gallery')

# Route for the gallery
@app.route('/gallery', methods=["GET", "POST"])
def gallery():
    icon_config = load_icon_config()
    available_icons = load_icons()

    if request.method == "POST":
        # Handle icon selection update
        app_name = request.form.get("app_name")
        selected_icon = request.form.get("icon_select")
        if app_name and selected_icon:
            icon_config[app_name] = selected_icon
            save_icon_config(icon_config)

    return render_template(
        "gallery.html",
        app_version=APP_VERSION,
        available_icons=available_icons,
        icon_config=icon_config
    )

# Route for Angel Investment Analysis
@app.route('/angel-investment-analysis')
def angel_investment_analysis():
    return render_template("index.html", app_version=APP_VERSION)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
