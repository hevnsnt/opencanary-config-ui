# OpenCanary Config UI

A Flask application to build and save an `opencanary.conf` via web form, covering all standard honeypot services and log handlers.

## Setup
1. Create and activate a Python 3 virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate


This is currently running at: https://opencanary-configure-4619d349657a.herokuapp.com/


$ 
sudo apt install virtualenv python3-dev python3-pip python3-virtualenv python3-venv python3-scapy libssl-dev libpcap-dev samba python3-virtualenvwrapper -y


nano ~/.bashrc
# Virtualenvwrapper settings
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh

source ~/.bashrc
mkvirtualenv opencanary
workon opencanary

$ pip install scapy pcapy-ng # if you plan to use the SNMP module
$ pip install opencanary


Creating the initial configuration

When OpenCanary starts it looks for config files in the following locations and will stop when the first configuration is found:

    ./opencanary.conf (i.e. the directory where OpenCanary is installed)
    ~/.opencanary.conf (i.e. the home directory of the user, usually this will be root so /root/.opencanary.conf)
    /etc/opencanaryd/opencanary.conf

To create an initial configuration, run as root (you may be prompted for a sudo password):
