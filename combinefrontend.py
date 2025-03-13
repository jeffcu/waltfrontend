import os
import mimetypes

def combine_frontend_files(base_directory, output_file):
    """Combines specific frontend file types from a Flutter project,
       excluding build directories, and lists assets."""

    text_extensions = ['.dart', '.yaml', '.yml', '.json', '.xml', '.txt'] # Flutter specific text file types
    asset_dir = "assets" # Flutter asset directory name
    build_dirs = ['.git', 'build', 'ios/build', 'android/build', '.pub-cache'] # Common Flutter build/cache directories

    asset_files = []
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Traverse the entire directory tree
        for root, dirs, files in os.walk(base_directory):
            # Remove build directories from walk to avoid traversing them
            dirs[:] = [d for d in dirs if d not in build_dirs]

            for filename in files:
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, base_directory)
                root_path = os.path.relpath(root, base_directory)


                # Skip .git and build directories
                if '.git' in relative_path.split(os.sep) or any(build_dir in root_path.split(os.sep) for build_dir in build_dirs):
                    continue

                _, ext = os.path.splitext(filename)
                if ext in text_extensions:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write(f"\n\n--- FILE: {relative_path} ---\n\n")
                            outfile.write(content)
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")
                # Handle asset files if the file is directly under assets, or a folder under assets
                elif asset_dir in relative_path.split(os.sep):
                    file_mime_type, _ = mimetypes.guess_type(filepath)
                    asset_files.append((relative_path, file_mime_type or 'unknown'))

        # Write the list of asset files to the end of the output file
        outfile.write("\n\n--- ASSET FILES ---\n\n")
        for path, mime_type in asset_files:
            outfile.write(f"File: {path}, Mime Type: {mime_type}\n")

if __name__ == "__main__":
    base_directory = "."  # Project Root - where the script runs (Flutter project root)
    output_file = "combined_frontend.txt"
    combine_frontend_files(base_directory, output_file)
    print(f"Combined frontend files into {output_file}")
