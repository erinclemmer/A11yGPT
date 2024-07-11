import os
import zipfile
import shutil

def unzip_and_collect_index(source_folder, destination_folder):
    # Ensure the source folder path exists
    if not os.path.exists(source_folder):
        print(f"The source folder '{source_folder}' does not exist.")
        return

    # Create the destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    # Iterate through all files in the source folder
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder, filename)
        
        # Check if the file is a ZIP file
        if filename.endswith('.zip') and os.path.isfile(file_path):
            # Create a temporary folder for extraction
            temp_extract_path = os.path.join(source_folder, 'temp_extract')
            os.makedirs(temp_extract_path, exist_ok=True)
            
            # Extract the ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                print(f"Extracting: {filename}")
                zip_ref.extractall(temp_extract_path)
            
            # Look for index.html in the extracted folder
            for root, dirs, files in os.walk(temp_extract_path):
                for file in files:
                    if '.html' in file:
                        index_path = os.path.join(root, file)
                        # Move index.html to the destination folder with a unique name
                        new_name = f"index_{filename[:-4]}.html"
                        shutil.move(index_path, os.path.join(destination_folder, new_name))
                        print(f"Moved index.html from {filename} to {destination_folder}")
                        break
            
            # Clean up: remove the temporary extraction folder
            shutil.rmtree(temp_extract_path)

    print("All ZIP files have been processed.")

# Example usage
source_folder = 'Projects'
destination_folder = 'html'
unzip_and_collect_index(source_folder, destination_folder)