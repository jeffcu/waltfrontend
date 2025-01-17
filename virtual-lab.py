import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    """Renders the main page with the user query input and displays the responses."""
    responses = []
    error = ""

    if request.method == 'POST':
        logger.info("Received a POST request.")
        # Get user input
        user_query = request.form['user_query']
        logger.info(f"User query: {user_query}")

        uploaded_files = request.files.getlist('uploaded_files')
        logger.info(f"Number of files uploaded: {len(uploaded_files)}")

        # Read content from uploaded files
        file_content = ""
        for file in uploaded_files:
            if file.filename:
                logger.info(f"Processing file: {file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                with open(filepath, 'r') as f:
                    file_content += f.read() + "\n"

        # Combine user query and file content
        combined_content = f"User Query: {user_query}\n\nUploaded Content:\n{file_content}"
        logger.info("Combined content created.")

        # Generate prompts and make API calls
        try:
            logger.info("Starting API calls...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = [
                call_openai_api(prompt.format(content=combined_content)) for _, prompt in PREDEFINED_PROMPTS
            ]
            responses = loop.run_until_complete(asyncio.gather(*tasks))
            loop.close()
            logger.info("API calls completed.")
        except Exception as e:
            logger.error(f"Error during API calls: {e}")
            error = str(e)

        # Format responses with titles
        responses = [
            {"title": title, "response": response}
            for (title, _), response in zip(PREDEFINED_PROMPTS, responses)
        ]

        # Check for errors in API calls
        if any("Error:" in res["response"] for res in responses):
            error = "One or more API calls failed. Check the responses."

    return render_template('index.html', responses=responses, error=error)
