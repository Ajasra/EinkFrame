import os
import sys
import time
import random

from PIL import Image, ImageFont, ImageDraw

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')

if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd4in2_V2

import image_processor


class DisplayManager:

    epd = None

    def __init__(self, settings, image_processor):
        self.settings = settings
        self.epd = epd4in2_V2.EPD()
        print("init and Clear")
        self.epd.init()
        self.epd.Clear()
        self.epd.init_fast(self.epd.Seconds_1_5S)
        random.seed(time.time())

        self.image_processor = image_processor

    def show_netimage(self, config, last_network, last_update_image):
        """
        Display the last created image from the 'netimage' folder.
        :return:
        """
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        netimage_folder_path = os.path.join(current_file_path, 'netimage')
        image = self.image_processor.get_last_created_image(netimage_folder_path)
        if image:
            Himage = Image.open(image)
            self.epd.display(self.epd.getbuffer(Himage))
        last_network = time.time() + config['refresh_rate'] * 10
        last_update_image = time.time() + config['refresh_rate'] * 2
        return last_network, last_update_image


    def show_next_image(self, cur, folder_name, config, last_update_image, rnd=False):
        """
        Display the next image from the specified folder.
        :param cur:
        :param folder_name:
        :param rnd:
        :return:
        """
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        if folder_name == self.settings.specific_folder:
            folder = os.path.join(current_file_path, folder_name)
        else:
            image_folder_path = os.path.join(current_file_path, folder_name)
            folder = self.image_processor.get_last_created_folder(image_folder_path)
        images = self.image_processor.get_all_images(folder)
        if images and images[cur]:
            Himage = Image.open(images[cur])
            self.epd.display(self.epd.getbuffer(Himage))
            if rnd:
                random.seed(time.time())
                cur = random.randint(0, len(images) - 1)
            else:
                cur = cur + 1
                if cur >= len(images):
                    cur = 0
        last_update_image = time.time() + config['refresh_rate']
        return cur, last_update_image

    def show_info(self, config, network_manager):
        """
        Display the current IP address on the e-ink display.
        :return:
        """
        font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
        Limage = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Limage)
        draw.text((10, 0), 'Loading', font=font24, fill=0)
        ip_address = network_manager.get_ip_address('wlan0')
        draw.text((10, 30), "ip: {}".format(ip_address), font=font24, fill=0)
        # print all config values in format key: value
        if config:
            y = 60
            for key, value in config.items():
                draw.text((10, y), f"{key}: {value}", font=font24, fill=0)
                y = y + 30
        self.epd.display(self.epd.getbuffer(Limage))


    def show_mode_info(self, mode, last_update_image, network_manager):
        font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
        Limage = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Limage)
        if mode == 0:
            draw.text((10, 0), 'mode 0', font=font24, fill=0)
        elif mode == 1:
            draw.text((10, 0), 'mode 1', font=font24, fill=0)
        elif mode == 2:
            draw.text((10, 0), 'mode 2', font=font24, fill=0)
        ip_address = network_manager.get_ip_address('wlan0')
        draw.text((10, 30), ip_address, font=font24, fill=0)
        self.epd.display(self.epd.getbuffer(Limage))
        last_update_image = 0
        time.sleep(2)
        return last_update_image

    def exit(self):
        self.epd.epdconfig.module_exit(cleanup=True)
