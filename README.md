
# E-Ink Display
E-Ink Display for Raspberry Pi based on Waveshare e-Paper library and 4.2 inch e-Paper display.

## Installation
1. Install raspbian on a Raspberry Pi
2. Update the system
```bash
sudo apt-get update
sudo apt-get upgrade
```
3. Install the required packages
```bash
sudo apt install git python3-pip python3-pil python3-numpy python3-spidev -y
```
4. Enable SPI
```bash
sudo raspi-config
```
Interfacing Options -> SPI -> Yes -> Finish -> Reboot
5. You can get the e-ink display library from the following link
```bash
git clone https://github.com/waveshare/e-Paper.git
```
With examples in 'e-Paper/RaspberryPi_JetsonNano/python/examples/'
Or you can clone this repository (include only python package for raspberry pi)
```bash
git clone https://github.com/Ajasra/EinkFrame.git
```
6. Install additional packages
```bash
pip install RPi.GPIO requests Pillow numpy
```

## Usage

### Auto Start on Boot

1. Create a new systemd service file:
```bash
sudo nano /lib/systemd/system/eink.service
```
2. Enable the service to start on boot:
```bash
sudo systemctl enable my_script.service
```
3. Start the service:
```bash
sudo systemctl start my_script.service
```
4. To stop the service for changes:
```bash
sudo systemctl stop eink.service
```
5. Reload the systemd manager configuration after making changes and before starting the service:
```bash
sudo systemctl daemon-reload
```
6. Start the service after making changes:
```bash
sudo systemctl start eink.service
```

Additional useful commands for testing and debugging:
```bash
# Reload the systemd manager configuration:
sudo systemctl daemon-reload
# Start the service manually:
sudo systemctl start eink.service
# Check the status of the service:
sudo systemctl status eink.service
# Check the logs for any errors:
sudo journalctl -u eink.service
# Reboot the Raspberry Pi to ensure the service starts on boot:
sudo reboot
```