# wolweb

Prosty panel webowy do budzenia urządzeń przez Wake-on-LAN.  
Napisany w Pythonie (Flask), zaprojektowany do działania na Raspberry Pi 4.

## Stack

- Python 3 + Flask
- Bootstrap 5 (CDN)
- `wakeonlan` (apt)

## Wymagania

```bash
sudo apt install wakeonlan python3-flask -y
```

## Instalacja

```bash
# Skopiuj aplikację
sudo mkdir -p /opt/wolweb
sudo cp app.py /opt/wolweb/

# Skonfiguruj urządzenia
sudo mkdir -p /etc/wolweb
sudo cp devices.example.json /etc/wolweb/devices.json
sudo nano /etc/wolweb/devices.json

# Zainstaluj jako systemd service
sudo cp wolweb.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wolweb
```

Panel dostępny na `http://<ip-rpi>:8089`

## Konfiguracja urządzeń

Edytuj `/etc/wolweb/devices.json`:

```json
{
  "devices": [
    {
      "name": "Desktop",
      "mac": "AA:BB:CC:DD:EE:FF"
    },
    {
      "name": "Proxmox",
      "mac": "11:22:33:44:55:66"
    }
  ]
}
```

> `devices.json` jest w `.gitignore` — MACi urządzeń nie trafiają do repo.
