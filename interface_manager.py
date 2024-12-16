import RPi.GPIO as GPIO
import time
import subprocess
class InterfaceManager:

    previous_button_state = 0
    button_pressed_time = 0 # time when button was pressed
    
    def __init__(self, settings):
        self.settings = settings
        GPIO.setwarnings(self.settings.gpio_warnings)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.settings.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.previous_button_state = GPIO.input(self.settings.button_pin)

    def shutdown_m(self):
        """
        Shutdown the Raspberry Pi.
        :return:
        """
        try:
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        except Exception as e:
            print(f"Error: {e}")

    def read_button(self, mode, last_update_image, network_manager, display_manager):
        """
        Read the state of the button and perform the appropriate action.
        :return:
        """
        try:
            button_state = GPIO.input(self.settings.button_pin)
            if button_state == GPIO.LOW:
                if self.button_pressed_time < time.time() and self.button_pressed_time != 0:
                    self.shutdown_m()
            if button_state != self.previous_button_state:
                self.previous_button_state = button_state
                if button_state == GPIO.LOW:
                    print("button pressed")
                    self.button_pressed_time = time.time() + self.settings.hold_to_shutdown
                else:
                    print("button released")
                    self.button_pressed_time = 0
                    mode = mode + 1
                    if mode > self.settings.max_modes:
                        mode = 0
                    last_update_image = display_manager.show_mode_info(mode, last_update_image, network_manager)
        except Exception as e:
            print(f"Error: {e}")
        return mode, last_update_image

    def cleanup(self):
        GPIO.cleanup()
