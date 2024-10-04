import datetime
import json
import os
import glob

from flask import Flask, request, render_template_string
from PIL import Image

app = Flask(__name__)

fields = {
    'mode': {
        'title': 'Current mode',
        'type': 'select',
        'options': [[0,'Folder'], [1,'Folder with online'], [2,'US']]
    },
    'refresh_rate': {
        'title': 'Update image interval',
        'type': 'number'
    },
    'random': {
        'title': 'Random',
        'type': 'checkbox'
    }
}

def process_and_save_image(image_path):
    """
    Load an image, scale it to maximize the crop area, crop it to 300x400 pixels (crop and fill),
    convert it to black and white, and save it as a 16-bit BMP file for an e-ink display.

    :param image_path: The path to the image file.
    :return: True if the image is processed and saved successfully, False otherwise.
    """
    try:
        # Load the image
        image = Image.open(image_path)
        # Get the original image size
        original_width, original_height = image.size
        # Calculate the scaling factor to maximize the crop area
        if original_width < original_height:
            scale_factor = 300 / original_width
        else:
            scale_factor = 400 / original_height
        # Scale the image
        scaled_width = int(original_width * scale_factor)
        scaled_height = int(original_height * scale_factor)
        scaled_image = image.resize((scaled_width, scaled_height), Image.ANTIALIAS)
        # Calculate the crop box to center the image
        left = (scaled_width - 300) / 2
        top = (scaled_height - 400) / 2
        right = (scaled_width + 300) / 2
        bottom = (scaled_height + 400) / 2
        # Crop the image to 300x400 pixels
        cropped_image = scaled_image.crop((left, top, right, bottom))
        # Convert the image to black and white
        bw_image = cropped_image.convert('1')
        # Save the image as a 16-bit BMP file
        bmp_image_path = os.path.splitext(image_path)[0] + '.bmp'
        bw_image.save(bmp_image_path, 'BMP')
        # Delete the original file
        os.remove(image_path)
        print('image converted')
        return True
    except Exception as e:
        print(f"Error processing and saving image: {e}")
        return False


def process_all_images_in_folder(folder_path):
    """
    Load all non-BMP images in the specified folder, process them, and save them as 16-bit BMP files.

    :param folder_path: The path to the folder containing the images.
    :return: True if all images are processed and saved successfully, False otherwise.
    """
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(current_file_path, folder_path)
    try:
        # Get a list of all non-BMP image files in the folder
        image_files = glob.glob(os.path.join(folder_path, '*'))
        non_bmp_images = [f for f in image_files if not f.lower().endswith('.bmp')]

        # Process each non-BMP image
        for image_path in non_bmp_images:
            if process_and_save_image(image_path):
                print(f"Processed and saved {image_path} successfully.")
            else:
                print(f"Failed to process and save {image_path}.")

        return True
    except Exception as e:
        print(f"Error processing images in folder: {e}")
        return False

# Load the config file
with open('config.txt', 'r') as f:
    config = json.load(f)

@app.route('/')
def home():
    form_html = '''
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            
        }
        .main-section {
            margin: auto;
            max-width: 600px;
        }
        h1 {
            color: #333;
        }
        form {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-top: 10px;
            font-weight: bold;
        }
        input[type="text"], input[type="file"], select {
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            box-sizing: border-box;
        }
        input[type="submit"] {
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
        .form-section {
            margin-bottom: 40px;
        }
    </style>
    <div class="main-section">
        <h1>Settings</h1>
        <div class="form-section">
            <form method="POST" action="/update">
                {% for key, field in fields.items() %}
                    <label for="{{ key }}">{{ field.title }}</label>
                    {% if field.type == 'select' %}
                        <select id="{{ key }}" name="{{ key }}">
                            {% for index, option in field.options %}
                                <option value="{{ index }}" {% if config[key] == index %}selected{% endif %}>{{ option }}</option>
                            {% endfor %}
                        </select>
                    {% elif field.type == 'number' %}
                        <input type="number" id="{{ key }}" name="{{ key }}" value="{{ config[key] }}">
                    {% elif field.type == 'checkbox' %}
                        <input type="checkbox" id="{{ key }}" name="{{ key }}" {% if config[key] %}checked{% endif %}>
                    {% else %}
                        <input type="text" id="{{ key }}" name="{{ key }}" value="{{ config[key] }}">
                    {% endif %}
                {% endfor %}
                <br>
                <input type="submit" value="Update">
            </form>
        </div>
        <h1>Upload Images</h1>
        <div class="form-section">
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <label for="images">Select images:</label>
                <input type="file" id="images" name="images" multiple><br>
                <input type="submit" value="Upload">
            </form>
        </div>
    </div>
    '''
    return render_template_string(form_html, config=config, fields=fields)

@app.route('/update', methods=['POST'])
def update():
    for key in config.keys():
        if key in fields:
            if fields[key]['type'] == 'checkbox':
                config[key] = key in request.form
            elif fields[key]['type'] == 'select':
                config[key] = int(request.form[key])
            elif fields[key]['type'] == 'number':
                config[key] = int(request.form[key])
            else:
                config[key] = request.form[key]
    with open('config.txt', 'w') as f:
        json.dump(config, f, indent=4)
    return '''
    Configuration updated successfully!<br>
    <a href="/">Return to Main Page</a>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("images")
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    path_to_save = 'images/{}/'.format(cur_date)

    # Create the directory if it doesn't exist
    if not os.path.exists(path_to_save):
        os.makedirs(path_to_save)

    for file in uploaded_files:
        file.save(f"{path_to_save}{file.filename}")

    # after images uploaded we need to process them
    process_all_images_in_folder(path_to_save)
    return '''
    Images uploaded successfully!<br>
    <a href="/">Return to Main Page</a>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)