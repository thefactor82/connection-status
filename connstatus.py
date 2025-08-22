import threading
import time
import ping3
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import tkinter as tk
import os
import json
import matplotlib.pyplot as plt  # <--- aggiungi questo import

# Configurazione ping3
ping3.EXCEPTIONS = True
ping3.DEBUG = False
ping3.privileged = False

# Percorso config cross-platform
def get_config_path():
    base = os.path.expanduser("~")
    if os.name == "nt":
        folder = os.path.join(base, "AppData", "Local", "ConnStatus")
    else:
        folder = os.path.join(base, "Library", "Application Support", "ConnStatus")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "config.json")

CONFIG_PATH = get_config_path()

# Config default
default_config = {
    "host": "google.it",
    "ping_interval": 2,
    "window": 1800,
    "thresholds": {
        "green": {"loss": 0.05, "latency": 100},
        "yellow": {"loss": 0.2, "latency": 200}
    }
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Errore caricamento config, uso default:", e)
    return default_config.copy()

def save_config(config):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Errore salvataggio config:", e)

config = load_config()
results = []

def create_icon(color):
    img = Image.new("RGB", (64, 64), color)
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    return img

icons = {c: create_icon(c) for c in ["green", "yellow", "red"]}

def ping_loop(icon):
    global results
    ICON_WINDOW = 5  # ultimi 5 ping per l'icona
    while True:
        try:
            latency = ping3.ping(config["host"], timeout=1)
            results.append((latency is not None, latency * 1000 if latency else None))
        except Exception:
            results.append((False, None))

        if len(results) > config["window"]:
            results = results[-config["window"]:]

        # Calcola statistiche per l'icona (ultimi 10 ping)
        recent = results[-ICON_WINDOW:] if len(results) >= ICON_WINDOW else results
        success = [r for r in recent if r[0]]
        loss = 1 - len(success) / len(recent) if recent else 1
        avg_latency = sum(r[1] for r in success if r[1]) / max(1, len(success))

        # Determina stato
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
                config["window"] = int(entry_window.get())  # <-- aggiungi questa riga
                save_config(config)
                root.destroy()
            except Exception as e:
                print("Errore salvataggio config:", e)

        root = tk.Tk()
        root.title("Impostazioni rete")
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        fields = [
            ("Host:", config["host"]),
            ("Green lat soglia (ms):", config["thresholds"]["green"]["latency"]),
            ("Yellow lat soglia (ms):", config["thresholds"]["yellow"]["latency"]),
            ("Green loss soglia (0-1):", config["thresholds"]["green"]["loss"]),
            ("Yellow loss soglia (0-1):", config["thresholds"]["yellow"]["loss"]),
            ("Window (numero ping da mantenere):", config["window"])  # <-- aggiungi questa riga
        ]
        entries = []
        for i, (label, value) in enumerate(fields):
            tk.Label(root, text=label).grid(row=i, column=0, sticky="w")
            entry = tk.Entry(root)
            entry.insert(0, value)
            entry.grid(row=i, column=1)
            entries.append(entry)

        entry_host, entry_green_lat, entry_yellow_lat, entry_green_loss, entry_yellow_loss, entry_window = entries  # <-- aggiungi entry_window

        tk.Button(root, text="Salva", command=save).grid(row=len(fields), column=0, columnspan=2)
        root.mainloop()

    threading.Thread(target=_run, daemon=True).start()

def show_graph():
    # Prendi i dati dell'ultima ora (window * ping_interval secondi)
    window_size = int(3600 / config["ping_interval"])
    data = results[-window_size:] if len(results) > window_size else results[:]
    times = list(range(-len(data)+1, 1))
    latencies = [r[1] if r[0] else None for r in data]

    # Determina colore per ogni punto
    colors = []
    for r in data:
        if not r[0]:
            colors.append("red")
        elif r[1] < config["thresholds"]["green"]["latency"]:
            colors.append("green")
        elif r[1] < config["thresholds"]["yellow"]["latency"]:
            colors.append("yellow")
        else:
            colors.append("red")

    plt.figure(figsize=(10, 4))
    plt.title("Andamento ping ultima ora")
    plt.xlabel("Ping (secondi fa)")
    plt.ylabel("Latency (ms)")
    plt.scatter(times, latencies, c=colors, s=10)
    plt.xlim(times[0], times[-1])
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def start():
    menu = Menu(
        MenuItem("Impostazioni", lambda icon, item: open_settings()),
        MenuItem("Grafico", lambda icon, item: threading.Thread(target=show_graph, daemon=True).start()),  # <--- nuova voce
        MenuItem("Esci", lambda icon, item: icon.stop())
    )
    icon = Icon("NetStatus", icons["green"], menu=menu)
    threading.Thread(target=ping_loop, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    start()
