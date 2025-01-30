from flask import Blueprint, request, jsonify
import openai
import logging

api_test_bp = Blueprint('api_test', __name__)
logging.basicConfig(level=logging.DEBUG)

def format_api_response(response_text):
    """Format response for structured readability."""
    formatted_text = response_text.replace("**", "")  # Remove double asterisks
    formatted_text = formatted_text.replace("\n", "<br>")  # Line breaks
    formatted_text = formatted_text.replace("- ", "<li>") + "</li>"  # Bullets
    formatted_text = formatted_text.replace("1. ", "<li><strong>1.</strong> ") + "</li>"  # Numbering
    return f"<strong>Analysis Report:</strong><br><ul>{formatted_text}</ul>"

@api_test_bp.route('/api_test', methods=['POST'])
def api_test():
    """Handles OpenAI API requests for the API Test popup."""
    data = request.json
    user_query = data.get('query', 'Who invented velcro?')

    if not user_query.strip():
        return jsonify({"response": "Error: Query is empty"}), 400

    try:
        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an API testing assistant."},
                {"role": "user", "content": user_query}
            ]
        )
        api_response = response.choices[0].message.content.strip()
        return jsonify({"response": format_api_response(api_response)})  # Apply formatting
    except Exception as e:
        logging.error(f"OpenAI API call failed: {str(e)}")
        return jsonify({"response": f"Error: {str(e)}"}), 500
