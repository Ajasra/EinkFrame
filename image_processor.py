import os
import glob
import requests
import shutil
import time
from PIL import Image

class ImageProcessor:
    """
    Class for processing images.
    """

    def __init__(self, settings):
        """
        Initialize the ImageProcessor with the given settings and logging.
        :param settings: The settings object.
        :param logging: The logging object.
        """
        self.settings = settings

    def copy_image_from_url(self, config):
        """
        Copy an image from a URL specified in the 'config.txt' file to the 'netimage' folder within the script's root directory.
        :param config: The configuration dictionary loaded from 'config.txt'.
        :return: True if the image is copied successfully, False otherwise.
        """
        try:
            # Check if 'url_image' exists in the config and is not empty
            if 'url_image' in config and config['url_image']:
                url_image = config['url_image']

                # Get the path of the current Python file
                current_file_path = os.path.dirname(os.path.abspath(__file__))
                netimage_folder_path = os.path.join(current_file_path, 'netimage')

                # Create the 'netimage' folder if it doesn't exist
                if not os.path.exists(netimage_folder_path):
                    os.makedirs(netimage_folder_path)

                # Download the image from the URL
                response = requests.get(url_image, stream=True, verify=False)
                response.raise_for_status()

                # Save the image to the 'netimage' folder
                image_filename = os.path.basename(url_image)
                image_path = os.path.join(netimage_folder_path, image_filename)

                with open(image_path, 'wb') as image_file:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, image_file)

                return True
            else:
                print("'url_image' not found or is empty in the config file.")
                return False
        except Exception as e:
            print(f"Error copying image from URL: {e}")
            return False


    def process_and_save_image(self, image_path):
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
                scale_factor = self.settings.epd_width / original_width
            else:
                scale_factor = self.settings.epd_height / original_height

            # Scale the image
            scaled_width = int(original_width * scale_factor)
            scaled_height = int(original_height * scale_factor)
            scaled_image = image.resize((scaled_width, scaled_height), Image.LANCZOS)

            # Calculate the crop box to center the image
            left = (scaled_width - self.settings.epd_width) / 2
            top = (scaled_height - self.settings.epd_height) / 2
            right = (scaled_width + self.settings.epd_width) / 2
            bottom = (scaled_height + self.settings.epd_height) / 2

            # Crop the image to 300x400 pixels
            cropped_image = scaled_image.crop((left, top, right, bottom))

            # Convert the image to black and white
            bw_image = cropped_image.convert('1')

            # Save the image as a 16-bit BMP file
            bmp_image_path = os.path.splitext(image_path)[0] + '.bmp'
            bw_image.save(bmp_image_path, 'BMP')

            # Delete the original file
            os.remove(image_path)

            print('Image converted and saved')
            return True
        except Exception as e:
            print(f"Error processing and saving image: {e}")
            return False


    def process_all_images_in_folder(self, folder_path):
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
                if self.process_and_save_image(image_path):
                    print(f"Processed and saved {image_path} successfully.")
                else:
                    print(f"Failed to process and save {image_path}.")

            return True
        except Exception as e:
            print(f"Error processing images in folder: {e}")
            return False


    def get_last_created_image(self, folder_path):
        """
        Get the last created image from the specified folder.

        :param folder_path: Path to the folder containing images.
        :return: The last created image file path, or None if no images are found.
        """
        # Use glob to find all image files in the folder
        image_files = glob.glob(os.path.join(folder_path, '*.bmp'))
        if not image_files:
            print("No image files found in the specified folder.")
            return False
        # Get the creation time of each image file and find the most recent one
        last_created_image = max(image_files, key=os.path.getctime)
        return last_created_image


    def get_all_images(self, folder_path):
        """
        Get all image files from the specified folder.

        :param folder_path: Path to the folder containing images.
        :return: A list of image file paths, or an empty list if no images are found.
        """
        # Use glob to find all image files in the folder
        image_files = glob.glob(os.path.join(folder_path, '*.bmp'))
        return image_files


    def get_last_created_folder(self, directory_path):
        """
        Get the last created folder from the specified directory.
        :param directory_path: Path to the directory containing folders.
        :return: The last created folder path, or None if no folders are found.
        """
        # Get all directories in the specified path
        directories = [d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))]
        if not directories:
            print("No folders found in the specified directory.")
            return []
        # Get the creation time of each directory and find the most recent one
        last_created_folder = max(directories, key=lambda d: os.path.getctime(os.path.join(directory_path, d)))
        return os.path.join(directory_path, last_created_folder)
