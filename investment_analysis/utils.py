def format_response(response_text):
    """
    Format API response for readability in the web UI.
    - Uses numbered sections (1., 2., 3.).
    - Each section has a subtitle, then a line break, then the content.
    """
    formatted_text = response_text.replace("**", "").replace("\n", "<br><br>")
    formatted_text = formatted_text.replace("1. ", "<strong>1. </strong>")
    formatted_text = formatted_text.replace("2. ", "<strong>2. </strong>")
    formatted_text = formatted_text.replace("3. ", "<strong>3. </strong>")
    formatted_text = formatted_text.replace("4. ", "<strong>4. </strong>")
    formatted_text = formatted_text.replace("5. ", "<strong>5. </strong>")

    return f"<strong>Analysis Report:</strong><br>{formatted_text}"

def format_pdf_content(summary_data):
    """
    Format content for structured PDF output.
    - Uses numbered sections (1., 2., 3.).
    - Ensures section numbers are followed by subtitles and content.
    - Sections are spaced out for readability.
    """
    formatted_text = summary_data.replace("**", "")
    formatted_text = formatted_text.replace("\n\n", "<br><br>")
    formatted_text = formatted_text.replace("1. ", "<div class='section'><span class='section-number'>1.</span> <span class='subtitle'>Introduction</span><br><div class='content'>")
    formatted_text = formatted_text.replace("2. ", "</div><div class='section'><span class='section-number'>2.</span> <span class='subtitle'>Market Analysis</span><br><div class='content'>")
    formatted_text = formatted_text.replace("3. ", "</div><div class='section'><span class='section-number'>3.</span> <span class='subtitle'>Financial Overview</span><br><div class='content'>")
    formatted_text = formatted_text.replace("4. ", "</div><div class='section'><span class='section-number'>4.</span> <span class='subtitle'>Competitive Landscape</span><br><div class='content'>")
    formatted_text = formatted_text.replace("5. ", "</div><div class='section'><span class='section-number'>5.</span> <span class='subtitle'>Conclusion</span><br><div class='content'>")

    return formatted_text + "</div>"
