# How to install

Create a new venv
```
python3 -m venv venv
```

Activate the venv
```
source venv/bin/activate
```

Install all python dependencies
```
python3 -m pip install -r requirements.txt
```

Ensure that user is added to dialout (if this wasn't the case, reboot is needed)
```
sudo adduser USERNAME dialout
```

Ensure that you can write to the printer
```
sudo echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="28e9", ATTRS{idProduct}=="0289", MODE="0664", GROUP="dialout"' > /etc/udev/rules.d/99-escpos.rules
sudo service udev restart
sudo udevadm control --reload
```

Move the service files to the right spot
```
sudo cp telegraph.service /lib/systemd/system/
sudo cp sql_app/telegraph-database.service /lib/systemd/system/
```

Force systemd to recognise these files
```
sudo systemctl daemon-reload
```

Enable both of them (this will ensure that they auto-boot)
```
sudo systemctl enable telegraph.service
sudo systemctl enable telegraph-database.service
```
