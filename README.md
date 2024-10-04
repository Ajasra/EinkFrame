
# E-Ink Display


## Installation


## Usage

### Auto Start on Boot

Create a new systemd service file:
'''sudo nano /lib/systemd/system/eink.service'''

Enable the service to start on boot:
'''sudo systemctl enable my_script.service'''
Start the service:
'''sudo systemctl start my_script.service'''


Reload the systemd manager configuration:
sudo systemctl daemon-reload
Start the service manually:
sudo systemctl start eink.service
Check the status of the service:
sudo systemctl status eink.service
Check the logs for any errors:
sudo journalctl -u eink.service
Reboot the Raspberry Pi to ensure the service starts on boot:
sudo reboot


To stop the service for changes:
'''sudo systemctl stop eink.service'''

Reload the systemd manager configuration after making changes and before starting the service:
'''sudo systemctl daemon-reload'''

Start the service after making changes:
'''sudo systemctl start eink.service'''