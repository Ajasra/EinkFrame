import subprocess
import os
from datetime import datetime
import shutil
import time
import json
import image_processor

class ConfigManager:

    last_modified_time = 0
    config = None

    def __init__(self, settings):
        """
        Initialize the ConfigManager with the given settings and logging.
        :param settings: The settings object.
        :param logging: The logging object.
        """
        self.settings = settings
        self.image_processor = image_processor.ImageProcessor(self.settings)

    def get_image_processor(self):
        """
        Get the image processor object.
        :return: The image processor object.
        """
        return self.image_processor

    def get_settings(self):
        """
        Get the settings object.
        :return: The settings object.
        """
        return self.settings

    def update_settings(self, settings):
        """
        Update the settings object.
        :param settings: The new settings object.
        """
        self.settings = settings

    def is_usb_device_mounted(self):
        """
        Check if a USB device is mounted in the /media/vasily directory.

        :return: True if a USB device is mounted, False otherwise.
        """
        try:
            # Check if the mount point exists and is a directory
            if os.path.exists(self.settings.mount_point) and os.path.isdir(self.settings.mount_point):
            # List the contents of the mount point
            contents = os.listdir(self.settings.mount_point)
            for item in contents:
                item_path = os.path.join(self.settings.mount_point, item)
                    if os.path.isdir(item_path):
                        return item
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def check_usb_content(self):
        """
        Check if the 'images' folder and 'config.txt' and 'wifi.txt' files exist on the USB device mounted in /media/vasily.

        :return: A dictionary indicating the presence of each item.
        """
        device_name = self.is_usb_device_mounted()
        if device_name:
            print("device connected: {}".format(device_name))

            mount_point = "{}/{}".format(self.settings.mount_point, device_name)
            usb_images_folder = os.path.join(self.settings.mount_point, 'images')
            wifi_file_path = os.path.join(self.settings.mount_point, 'wifi.txt')
            config_file_path = os.path.join(self.settings.mount_point, 'config.txt')

            # Check if the mount point exists and is a directory
            if os.path.exists(self.settings.mount_point) and os.path.isdir(self.settings.mount_point):
                # List the contents of the mount point
                contents = os.listdir(self.settings.mount_point)

                # Check if the 'images' folder exists on the USB device
                if os.path.exists(usb_images_folder) and os.path.isdir(usb_images_folder):
                    # Get the current date in the format YYYY-MM-DD
                    current_date = datetime.now().strftime('%Y-%m-%d')

                    # Get the path of the current Python file
                    current_file_path = os.path.dirname(os.path.abspath(__file__))
                    destination_folder = os.path.join(current_file_path, 'images', current_date)

                    # Create the destination folder if it doesn't exist
                    os.makedirs(destination_folder, exist_ok=True)

                    # Copy the contents of the 'images' folder to the destination folder
                    try:
                        i = 0
                        for item in os.listdir(usb_images_folder):
                            src_item = os.path.join(usb_images_folder, item)
                            dst_item = os.path.join(destination_folder, item)
                            if os.path.isdir(src_item):
                                shutil.copytree(src_item, dst_item)
                            else:
                                shutil.copy2(src_item, dst_item)
                            i = i + 1
                        print("{} images coppied to {}".format(i, destination_folder))

                        self.image_processor.process_all_images_in_folder(destination_folder)
                    except Exception as e:
                        print(f"Error copying files: {e}")
                else:
                    print("There no new images")

                # Check if the 'config.txt' file exists on the USB device
                if os.path.exists(config_file_path) and os.path.isfile(config_file_path):
                    try:
                        # Get the path of the current Python file
                        current_file_path = os.path.dirname(os.path.abspath(__file__))
                        destination_file_path = os.path.join(current_file_path, 'config.txt')

                        # Copy the 'config.txt' file to the current script's root directory
                        shutil.copy2(config_file_path, destination_file_path)

                        print("Config updated")
                    except Exception as e:
                        print(f"Error copying config file: {e}")
                else:
                    print("No new config file")

                # Check if the 'wifi.txt' file exists on the USB device
                if os.path.exists(wifi_file_path) and os.path.isfile(wifi_file_path):
                    try:
                        # Read the contents of the 'wifi.txt' file
                        with open(wifi_file_path, 'r') as wifi_file:
                            wifi_config = wifi_file.read()

                        # Update the Wi-Fi configuration file
                        wpa_supplicant_path = self.settings.wifi_config_path
                        with open(wpa_supplicant_path, 'a') as wpa_file:
                            wpa_file.write(wifi_config)

                        # Restart the networking service to apply the changes
                        try:
                            subprocess.run(['sudo', 'wpa_cli', 'reconfigure'], check=True)
                        except Exception as e:
                            print(f"Error: {e}")

                        print("wifi updated")
                        os.rename(wifi_file_path, os.path.join(mount_point, 'wifi_processed.txt'))

                    except Exception as e:
                        print(f"Error updating Wi-Fi settings: {e}")
                else:
                    print("No wifi changes")

            return True

        else:
            return False


    def load_config_file(self):
        """
        Load the 'config.txt' file from the root directory of the current script.
        :return: The contents of the 'config.txt' file as a dictionary, or None if the file does not exist or cannot be loaded.
        """
        try:
            # Get the path of the current Python file
            current_file_path = os.path.dirname(os.path.abspath(__file__))
            config_file_path = os.path.join(current_file_path, 'config.txt')

            # Check if the 'config.txt' file exists
            if os.path.exists(config_file_path) and os.path.isfile(config_file_path):
                # Load the contents of the 'config.txt' file
                with open(config_file_path, 'r') as config_file:
                    config_data = json.load(config_file)
                print("Config loaded")
                return config_data
            else:
                print("No 'config.txt' file found in the script's root directory.")
                return None
        except Exception as e:
            print(f"Error loading config file: {e}")
            return None

    def update_config(self):
        """
        Update the configuration settings from the 'config.txt' file and process any new images from the USB device.
        :return:
        """
        self.check_usb_content()
        self.config = self.load_config_file()
        if self.config:
            new_image = self.image_processor.copy_image_from_url(self.config)
            if new_image:
                self.image_processor.process_all_images_in_folder('netimage')

        self.last_modified_time = time.time() + self.update_config_every
            
