# money-dashboard

[![PyPI - Version](https://img.shields.io/pypi/v/money-dashboard.svg)](https://pypi.org/project/money-dashboard)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/money-dashboard.svg)](https://pypi.org/project/money-dashboard)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

Installation on Raspberry Pi 2 running **Raspberry Pi OS lite 32 bit 'bookworm'**

1) Install Python 3.12 (build from source)
```
wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev  libsqlite3-dev
tar -xzvf Python-3.12.2.tgz 
cd Python-3.12.2/
./configure --enable-optimizations
sudo make altinstall  # need altinstall to install to /usr/local/bin/python3.12 rather than the system Python folder
```
2) Install `money-dashboard`
```
git clone https://github.com/nibuman/money_dashboard.git
cd money_dashboard/
# Numpy won't pip install, so install a system-wide package
sudo apt install python3-pandas python3-numpy
# Create a venv that can access system-wide packages
python3 -m venv --system-site-packages venv
source  venv/bin/activate
# Install the remaining packages into the venv
python3 -m pip install dash dash_mantine_components

```
At this point, should be able to see the app by running `python3 app.py` and going to `server_ip:8050` from another computer on the network

3) Set up gunicorn service
```
sudo apt install gunicorn
python3 -m gunicorn --bind 0.0.0.0:5000 wsgi:server
```
Check that dashboard accessible on `server_ip:5000`
Create systemd service file:
**`/etc/systemd/system/money_dashboard.service`**
```
[Unit]
Description=Gunicorn instance to server money_dashboard
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/<username>/money_dashboard
Environment="PATH=/home/<username>/money_dashboard/venv/bin"
ExecStart=/home/<username>/money_dashboard/venv/bin/python3 -m gunicorn --workers 3 --bind unix:money_dashboard.sock -m 007 wsgi:server

[Install]
WantedBy=multi-user.target
```

## License

`money-dashboard` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
