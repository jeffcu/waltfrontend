import os
import mimetypes

def combine_files(base_directory, output_file):
    """Combines specific file types, excluding the .venv directory,
       and lists static files in the static directory."""

    text_extensions = ['.py', '.html', '.txt', '.env', '.json', '.css', '.js', '.xml', 'Procfile']
    static_dir = "static"
    venv_dir = ".venv"  # Name of your virtual environment directory

    static_files = []
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Traverse the entire directory tree
        for root, _, files in os.walk(base_directory):
            for filename in files:
                filepath = os.path.join(root, filename) # Correct file path

                relative_path = os.path.relpath(filepath, base_directory) # Relative to project root
                root_path = os.path.relpath(root, base_directory)
                #filename=os.path.basename(filepath) #Get File Name #Unnecessary now

                # Skip .git directory, and .venv directory
                if '.git' in relative_path.split(os.sep) or venv_dir in root_path.split(os.sep):
                    continue

                _, ext = os.path.splitext(filename) #Get extension
                if ext in text_extensions or filename == 'Procfile':
                    try:
                        with open(filepath, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write(f"\n\n--- FILE: {relative_path} ---\n\n")
                            outfile.write(content)
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")
                # Handle static files if the file is directly under static, or a folder under static
                elif static_dir in relative_path.split(os.sep):
                    # Handle static files
                    file_mime_type, _ = mimetypes.guess_type(filepath)
                    static_files.append((relative_path, file_mime_type or 'unknown'))

        # Write the list of static files to the end of the output file
        outfile.write("\n\n--- STATIC FILES ---\n\n")
        for path, mime_type in static_files:
            outfile.write(f"File: {path}, Mime Type: {mime_type}\n")


if __name__ == "__main__":
    base_directory = "."  # Project Root - where the script runs
    output_file = "combined_project.txt"
    combine_files(base_directory, output_file)
    print(f"Combined files into {output_file}")
