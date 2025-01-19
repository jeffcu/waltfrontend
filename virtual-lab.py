from flask import Flask, render_template, redirect, request, jsonify
import os
import json

app = Flask(__name__)

# Global variable for app version
APP_VERSION = "0.2.0"

# Load the icon configuration
ICON_CONFIG_FILE = "icon_config.json"

def load_icon_config():
    if not os.path.exists(ICON_CONFIG_FILE):
        # Create a default config if none exists
        default_config = {
            "Angel Investment Analysis": "dewar-flask.jpeg"
        }
        with open(ICON_CONFIG_FILE, "w") as f:
            json.dump(default_config, f)
    with open(ICON_CONFIG_FILE, "r") as f:
        return json.load(f)

def save_icon_config(config):
    with open(ICON_CONFIG_FILE, "w") as f:
        json.dump(config, f)

@app.route('/')
def home():
    # Redirect to the gallery as the default page
    return redirect('/gallery')

@app.route('/gallery', methods=["GET", "POST"])
def gallery():
    icon_config = load_icon_config()
    if request.method == "POST":
        app_name = request.form.get("app_name")
        icon = request.form.get("icon")
        if app_name and icon:
            icon_config[app_name] = icon
            save_icon_config(icon_config)
    return render_template('gallery.html', icon_config=icon_config, app_version=APP_VERSION)

@app.route('/angel-investment-analysis')
def angel_investment_analysis():
    return render_template('angel_investment_analysis.html', app_version=APP_VERSION)

@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

if __name__ == "__main__":
    app.run(debug=True)
