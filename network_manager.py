import socket
import zlib
import numpy as np
import cv2
from PIL import Image
import struct
import fcntl

class NetworkManager:

    s = None

    def __init__(self, settings):
        self.settings = settings

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
            self.s.bind((self.settings.touchdesigner_ip, self.settings.touchdesigner_port))
            self.s.listen()


    def update_settings(self, settings):
        self.settings = settings


    def receive_frame(self, epd):
        conn, addr = self.s.accept()
            
        with conn:
            try:
                frame_data = b''
                expected_size = self.settings.epd_width * self.settings.epd_height
                while len(frame_data) < expected_size:
                    chunk = conn.recv(expected_size - len(frame_data))
                    if not chunk:
                        print("Incomplete frame received")
                        break
                    frame_data += chunk
                
                frame_data = zlib.decompress(frame_data)
                
                if len(frame_data) != expected_size:
                    print("Frame size mismatch")
                    return
                
                frame = np.frombuffer(frame_data, dtype=np.uint8).reshape(self.settings.epd_height, self.settings.epd_width)
                
                # Convert the frame to the correct format for the e-ink display
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                frame = cv2.resize(frame, (self.settings.epd_height, self.settings.epd_width))
                
                    # Convert NumPy array to PIL Image
                frame_pil = Image.fromarray(frame)
                
                # Display the frame on the e-ink display
                epd.display(epd.getbuffer(frame_pil))
                #epd.sleep()
            except Exception as e:
                print(f"Error: {e}")
                return

    def get_ip_address(self, ifname):
        """
        Get the current IP address of the specified network interface.
        :param ifname: The name of the network interface (e.g., 'eth0' or 'wlan0').
        :return: The IP address as a string, or None if the interface is not found.
        """
        try:
            return socket.inet_ntoa(fcntl.ioctl(
                self.s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15].encode('utf-8'))
            )[20:24])
        except IOError:
            return 'undefined'


