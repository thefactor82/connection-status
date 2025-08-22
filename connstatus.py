import threading
import time
import ping3
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import tkinter as tk
import os
import json

ping3.EXCEPTIONS = True
ping3.DEBUG = False
ping3.privileged = False

# Percorso config cross-platform
def get_config_path():
    base = os.path.expanduser("~")
    if os.name == "nt":  # Windows
        folder = os.path.join(base, "AppData", "Local", "ConnStatus")
    else:  # macOS / Linux
        folder = os.path.join(base, "Library", "Application Support", "ConnStatus")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "config.json")

CONFIG_PATH = get_config_path()

# Config default
default_config = {
    "host": "google.it",
    "ping_interval": 2,
    "window": 10,
    "thresholds": {
        "green": {"loss": 0.05, "latency": 100},
        "yellow": {"loss": 0.2, "latency": 200}
    }
}

# Carica config da file se esiste
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except Exception as e:
        print("Errore caricamento config, uso default:", e)
        config = default_config.copy()
else:
    config = default_config.copy()

# Funzione per salvare config su file
def save_config():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Errore salvataggio config:", e)

results = []

def create_icon(color):
    img = Image.new("RGB", (64, 64), color)
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    return img

icons = {
    "green": create_icon("green"),
    "yellow": create_icon("yellow"),
    "red": create_icon("red")
}

def ping_loop(icon):
    global results
    while True:
        try:
            latency = ping3.ping(config["host"], timeout=1)
            if latency is None:
                results.append((False, None))
            else:
                results.append((True, latency * 1000))  # ms
        except Exception:
            results.append((False, None))

        if len(results) > config["window"]:
            results = results[-config["window"]:]

        # Stats
        success = [r for r in results if r[0]]
        loss = 1 - len(success) / len(results)
        avg_latency = sum(r[1] for r in success if r[1]) / max(1, len(success))

        # Decide color
        if loss <= config["thresholds"]["green"]["loss"] and avg_latency < config["thresholds"]["green"]["latency"]:
            state = "green"
        elif loss <= config["thresholds"]["yellow"]["loss"] and avg_latency < config["thresholds"]["yellow"]["latency"]:
            state = "yellow"
        else:
            state = "red"

        icon.icon = icons[state]
        time.sleep(config["ping_interval"])

def open_settings():
    def _run():
        def save():
            try:
                config["host"] = entry_host.get()
                config["thresholds"]["green"]["latency"] = int(entry_green_lat.get())
                config["thresholds"]["yellow"]["latency"] = int(entry_yellow_lat.get())
                config["thresholds"]["green"]["loss"] = float(entry_green_loss.get())
                config["thresholds"]["yellow"]["loss"] = float(entry_yellow_loss.get())
                save_config()  # salva su file
                root.destroy()
            except Exception as e:
                print("Errore salvataggio config:", e)

        root = tk.Tk()
        root.title("Impostazioni rete")

        # Chiudi correttamente con la X
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        tk.Label(root, text="Host:").grid(row=0, column=0, sticky="w")
        entry_host = tk.Entry(root)
        entry_host.insert(0, config["host"])
        entry_host.grid(row=0, column=1)

        tk.Label(root, text="Green lat soglia (ms):").grid(row=1, column=0, sticky="w")
        entry_green_lat = tk.Entry(root)
        entry_green_lat.insert(0, config["thresholds"]["green"]["latency"])
        entry_green_lat.grid(row=1, column=1)

        tk.Label(root, text="Yellow lat soglia (ms):").grid(row=2, column=0, sticky="w")
        entry_yellow_lat = tk.Entry(root)
        entry_yellow_lat.insert(0, config["thresholds"]["yellow"]["latency"])
        entry_yellow_lat.grid(row=2, column=1)

        tk.Label(root, text="Green loss soglia (0-1):").grid(row=3, column=0, sticky="w")
        entry_green_loss = tk.Entry(root)
        entry_green_loss.insert(0, config["thresholds"]["green"]["loss"])
        entry_green_loss.grid(row=3, column=1)

        tk.Label(root, text="Yellow loss soglia (0-1):").grid(row=4, column=0, sticky="w")
        entry_yellow_loss = tk.Entry(root)
        entry_yellow_loss.insert(0, config["thresholds"]["yellow"]["loss"])
        entry_yellow_loss.grid(row=4, column=1)

        tk.Button(root, text="Salva", command=save).grid(row=5, column=0, columnspan=2)
        root.mainloop()

    # Avvio la GUI in un nuovo thread, così non blocca la tray
    threading.Thread(target=_run, daemon=True).start()

def start():
    menu = Menu(
        MenuItem("Impostazioni", lambda icon, item: open_settings()),
        MenuItem("Esci", lambda icon, item: icon.stop())
    )
    icon = Icon("NetStatus", icons["green"], menu=menu)
    threading.Thread(target=ping_loop, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    start()
