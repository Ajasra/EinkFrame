class Settings:
    """
    Settings for the E-Ink Display
    """

    def __init__(self):
        """
        Initialize the settings with default values
        """
        self.mode = 0
        self.max_modes = 3
        self.update_config_every = 3600
        self.hold_to_shutdown = 3
        self.button_pin = 32
        self.gpio_warnings = False
        self.mount_point = '/media/vasily'
        self.epd_width = 400
        self.epd_height = 300
        self.wifi_config_path = '/etc/wpa_supplicant/wpa_supplicant.conf'
        self.touchdesigner_ip = '192.168.1.100'
        self.touchdesigner_port = 9000
        self.specific_folder = 'us'

"""
Modes:
0 - BASIC - display latest uploaded images
1 - NET - display images from network
2 - FOLDER - display images from specific folder
3 - SYNC - synchronize with another e-ink display over the network
4 - TD - display images from TouchDesigner
"""




