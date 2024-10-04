#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import shutil
import glob

print("STARTING")

import socket
import fcntl
import struct

from datetime import datetime
import time

import subprocess

import requests
import json
import random

from PIL import Image, ImageFont, ImageDraw

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')

if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd4in2_V2
import RPi.GPIO as GPIO

import settings

GPIO.setwarnings(settings.GPIO_WARNINGS)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(settings.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

mount_point = settings.MOUNT_POINT

config = None
last_modified_time = 0
last_update_image = 0
last_network = 0

mode = 0
previous_button_state = GPIO.input(settings.BUTTON_PIN)
button_pressed_time = 0

update_config_every = settings.UPDATE_CONFIG_EVERY
hold_to_shutdown = settings.HOLD_TO_SHUTDOWN
max_modes = settings.MAX_MODES

epd = epd4in2_V2.EPD()

logging.basicConfig(level=logging.DEBUG)


def shutdown_m():
    """
    Shutdown the Raspberry Pi.
    :return:
    """
    epd4in2_V2.epdconfig.module_exit(cleanup=True)
    GPIO.cleanup()
    subprocess.run(['sudo', 'shutdown', '-h', 'now'])


def is_usb_device_mounted():
    """
    Check if a USB device is mounted in the /media/vasily directory.

    :return: True if a USB device is mounted, False otherwise.
    """
    # Check if the mount point exists and is a directory
    if os.path.exists(mount_point) and os.path.isdir(mount_point):
        # List the contents of the mount point
        contents = os.listdir(mount_point)
        for item in contents:
            item_path = os.path.join(mount_point, item)
            if os.path.isdir(item_path):
                return item
    return False


def check_usb_content():
    """
    Check if the 'images' folder and 'config.txt' and 'wifi.txt' files exist on the USB device mounted in /media/vasily.

    :return: A dictionary indicating the presence of each item.
    """
    device_name = is_usb_device_mounted()
    if device_name:
        logging.info("device connected: {}".format(device_name))

        usb_drive = "{}/{}".format(mount_point, device_name)
        usb_images_folder = os.path.join(usb_drive, 'images')
        wifi_file_path = os.path.join(usb_drive, 'wifi.txt')
        config_file_path = os.path.join(usb_drive, 'config.txt')

        # Check if the mount point exists and is a directory
        if os.path.exists(usb_drive) and os.path.isdir(usb_drive):
            # List the contents of the mount point
            contents = os.listdir(usb_drive)

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
                    logging.info("{} images coppied to {}".format(i, destination_folder))

                    process_all_images_in_folder('images/{}'.format(current_date))
                except Exception as e:
                    logging.info(f"Error copying files: {e}")
            else:
                logging.info("There no new images")

            # Check if the 'config.txt' file exists on the USB device
            if os.path.exists(config_file_path) and os.path.isfile(config_file_path):
                try:
                    # Get the path of the current Python file
                    current_file_path = os.path.dirname(os.path.abspath(__file__))
                    destination_file_path = os.path.join(current_file_path, 'config.txt')

                    # Copy the 'config.txt' file to the current script's root directory
                    shutil.copy2(config_file_path, destination_file_path)

                    logging.info("Config updated")
                except Exception as e:
                    logging.info(f"Error copying config file: {e}")
            else:
                logging.info("No new config file")

            # Check if the 'wifi.txt' file exists on the USB device
            if os.path.exists(wifi_file_path) and os.path.isfile(wifi_file_path):
                try:
                    # Read the contents of the 'wifi.txt' file
                    with open(wifi_file_path, 'r') as wifi_file:
                        wifi_config = wifi_file.read()

                    # Update the Wi-Fi configuration file
                    wpa_supplicant_path = settings.WIFI_CONFIG_PATH
                    with open(wpa_supplicant_path, 'a') as wpa_file:
                        wpa_file.write(wifi_config)

                    # Restart the networking service to apply the changes
                    subprocess.run(['sudo', 'wpa_cli', 'reconfigure'], check=True)

                    logging.info("wifi updated")
                    os.rename(wifi_file_path, os.path.join(usb_drive, 'wifi_processed.txt'))

                except Exception as e:
                    logging.info(f"Error updating Wi-Fi settings: {e}")
            else:
                logging.info("No wifi changes")

        return True

    else:
        return False


def load_config_file():
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
            logging.info("Config loaded")
            return config_data
        else:
            logging.info("No 'config.txt' file found in the script's root directory.")
            return None
    except Exception as e:
        logging.info(f"Error loading config file: {e}")
        return None


def copy_image_from_url():
    """
    Copy an image from a URL specified in the 'config.txt' file to the 'netimage' folder within the script's root directory.
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

            print(response)

            # Save the image to the 'netimage' folder
            image_filename = os.path.basename(url_image)
            image_path = os.path.join(netimage_folder_path, image_filename)

            with open(image_path, 'wb') as image_file:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, image_file)

            return True
        else:
            logging.info("'url_image' not found or is empty in the config file.")
            return False
    except Exception as e:
        logging.info(f"Error copying image from URL: {e}")
        return False


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
        logging.info('image converted')
        return True
    except Exception as e:
        logging.info(f"Error processing and saving image: {e}")
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
                logging.info(f"Processed and saved {image_path} successfully.")
            else:
                logging.info(f"Failed to process and save {image_path}.")

        return True
    except Exception as e:
        logging.info(f"Error processing images in folder: {e}")
        return False


def update_config():
    """
    Update the configuration settings from the 'config.txt' file and process any new images from the USB device.
    :return:
    """
    global config, last_modified_time, update_config_every
    check_usb_content()
    config = load_config_file()
    if config:
        new_image = copy_image_from_url()
        if new_image:
            process_all_images_in_folder('netimage')
    last_modified_time = time.time() + update_config_every


def get_last_created_image(folder_path):
    """
    Get the last created image from the specified folder.
    :param folder_path: Path to the folder containing images.
    :return: The last created image file path, or None if no images are found.
    """
    # Use glob to find all image files in the folder
    image_files = glob.glob(os.path.join(folder_path, '*.bmp'))
    if not image_files:
        logging.info("No image files found in the specified folder.")
        return False
    # Get the creation time of each image file and find the most recent one
    last_created_image = max(image_files, key=os.path.getctime)
    return last_created_image


def get_all_images(folder_path):
    """
    Get all image files from the specified folder.
    :param folder_path: Path to the folder containing images.
    :return: A list of image file paths, or an empty list if no images are found.
    """
    # Use glob to find all image files in the folder
    image_files = glob.glob(os.path.join(folder_path, '*.bmp'))
    return image_files


def get_last_created_folder(directory_path):
    """
    Get the last created folder from the specified directory.
    :param directory_path: Path to the directory containing folders.
    :return: The last created folder path, or None if no folders are found.
    """
    # Get all directories in the specified path
    directories = [d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))]
    if not directories:
        logging.info("No folders found in the specified directory.")
        return None
    # Get the creation time of each directory and find the most recent one
    last_created_folder = max(directories, key=lambda d: os.path.getctime(os.path.join(directory_path, d)))
    process_all_images_in_folder(os.path.join(directory_path, last_created_folder))

    return os.path.join(directory_path, last_created_folder)


def show_netimage():
    """
    Display the last created image from the 'netimage' folder.
    :return:
    """
    global last_network, config, last_update_image

    current_file_path = os.path.dirname(os.path.abspath(__file__))
    netimage_folder_path = os.path.join(current_file_path, 'netimage')
    image = get_last_created_image(netimage_folder_path)
    if image:
        Himage = Image.open(image)
        epd.display(epd.getbuffer(Himage))
    last_network = time.time() + config['refresh_rate'] * 10
    last_update_image = time.time() + config['refresh_rate'] * 2


def show_next_image(cur, folder_name, rand=False):
    """
    Display the next image from the specified folder.
    :param rand:
    :param cur:
    :param folder_name:
    :return:
    """
    global last_update_image, config
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    if folder_name == 'us':
        folder = os.path.join(current_file_path, folder_name)
    else:
        image_folder_path = os.path.join(current_file_path, folder_name)
        folder = get_last_created_folder(image_folder_path)
    images = get_all_images(folder)
    if images and images[cur]:
        Himage = Image.open(images[cur])
        epd.display(epd.getbuffer(Himage))
        if rand:
            random.seed(time.time())
            cur = random.randint(0, len(images) - 1)
            print(f"rand: {cur}")
        else:
            cur = cur + 1
            if cur >= len(images):
                cur = 0
    last_update_image = time.time() + config['refresh_rate']
    return cur


def get_ip_address(ifname='wlan0'):
    """
    Get the current IP address of the specified network interface.
    :param ifname: The name of the network interface (e.g., 'eth0' or 'wlan0').
    :return: The IP address as a string, or None if the interface is not found.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
    except IOError:
        return 'undefined'


def show_info():
    """
    Display the current IP address on the e-ink display.
    :return:
    """
    global epd, config, last_update_image

    font16 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 16)
    Limage = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
    draw = ImageDraw.Draw(Limage)
    if mode == 0:
        draw.text((10, 0), 'Uploaded images', font=font16, fill=0)
    elif mode == 1:
        draw.text((10, 0), 'Uploaded images + online', font=font16, fill=0)
    elif mode == 2:
        draw.text((10, 0), 'US', font=font16, fill=0)
    ip_address = get_ip_address('wlan0')
    draw.text((10, 30), "ip: {}".format(ip_address), font=font16, fill=0)
    # print all config values in format key: value
    if config:
        y = 60
        for key, value in config.items():
            draw.text((10, y), f"{key}: {value}", font=font16, fill=0)
            y = y + 30
    epd.display(epd.getbuffer(Limage))
    last_update_image = 0
    time.sleep(2)


def read_button():
    """
    Read the state of the button and perform the appropriate action.
    - short press: switch to the next mode
    - long press: shutdown the Raspberry Pi
    :return:
    """
    global previous_button_state, mode, button_pressed_time, hold_to_shutdown
    button_state = GPIO.input(32)
    if button_state == GPIO.LOW:
        if button_pressed_time < time.time() and button_pressed_time != 0:
            shutdown_m()
    if button_state != previous_button_state:
        previous_button_state = button_state
        if button_state == GPIO.LOW:
            print("button pressed")
            button_pressed_time = time.time() + hold_to_shutdown
        else:
            print("button released")
            button_pressed_time = 0
            mode = mode + 1
            if mode > max_modes:
                mode = 0
            show_info()


if __name__ == '__main__':

    try:
        logging.info("Starting")
        random.seed(time.time())
        config = load_config_file()
        update_config()

        logging.info("init and Clear")
        epd.init()
        epd.Clear()
        epd.init_fast(epd.Seconds_1_5S)
        show_info()

        time.sleep(5)
        epd.Clear()

        rnd = False
        cur_image = 0

        # setup mode on start, after switch with buttons
        if 'mode' in config and config['mode']:
            mode = config['mode']

        while True:
            if last_modified_time < time.time():
                update_config()
                if 'random' in config and config['random']:
                    rnd = True
            if 'refresh_rate' in config and config['refresh_rate']:
                if last_update_image < time.time():
                    if mode == 0:
                        cur_image = show_next_image(cur_image, 'images', rnd)
                    elif mode == 1:
                        if last_network < time.time():
                            show_netimage()
                        else:
                            cur_image = show_next_image(cur_image, 'images', rnd)
                    elif mode == 2:
                        if last_network < time.time():
                            show_netimage()
                        else:
                            cur_image = show_next_image(cur_image, 'us', rnd)
            read_button()
            time.sleep(0.1)

    except IOError as e:
        logging.info(e)

    except KeyboardInterrupt:
        # stop the program
        logging.info("ctrl + c:")
        epd4in2_V2.epdconfig.module_exit(cleanup=True)
        GPIO.cleanup()
        exit()
