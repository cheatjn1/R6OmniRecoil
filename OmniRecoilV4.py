import tkinter as tk
from tkinter import messagebox, ttk
import time
import random
import sys
import json
import os
import threading
import ctypes

# Constants
VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_CAPITAL = 0x14  # Caps Lock
VK_INSERT = 0x2D   # Insert = exit
MOUSEEVENTF_MOVE = 0x0001

user32 = ctypes.windll.user32

CONFIG_DIR = "configs"
CONFIG_FILE = "antirecoil_configs.json"

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)


class AntiRecoilApp:
    def __init__(self, master):
        self.master = master
        master.title("0MNI.REC0IL")
        master.geometry("420x500")
        master.configure(bg="#1e1e1e")  # Dark background
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.configs = self.load_configs()

        # ── Title ──
        tk.Label(master, text="0MNI.REC0IL", font=("Segoe UI", 30, "bold"),
                 bg="#1e1e1e", fg="white").pack(pady=(12, 0))
        tk.Label(master, text="made by fragment", font=("Segoe UI", 10),
                 bg="#1e1e1e", fg="white").pack(pady=(0, 12))

        # ── Config name + dropdown + save ──
        top_frame = tk.Frame(master, bg="#1e1e1e")
        top_frame.pack(pady=12, padx=12, fill="x")

        tk.Label(top_frame, text="Config name:", bg="#1e1e1e", fg="white").pack(side="left", padx=(0, 6))

        self.name_entry = tk.Entry(top_frame, bg="white", fg="black")
        self.name_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.name_entry.insert(0, "New Config")

        tk.Button(top_frame, text="Save", width=8, command=self.save_config).pack(side="right")

        tk.Label(top_frame, text="Load:", bg="#1e1e1e", fg="white").pack(side="left", padx=(12, 4))

        self.config_combo = ttk.Combobox(
            top_frame,
            values=list(self.configs.keys()),
            state="readonly",
            width=18
        )
        self.config_combo.pack(side="left", fill="x")
        self.config_combo.bind("<<ComboboxSelected>>", self.on_combo_select)

        # ── Settings ──
        settings_frame = tk.LabelFrame(
            master,
            text="Settings (decimals allowed)",
            padx=12,
            pady=12,
            bg="#1e1e1e",
            fg="white",
            labelanchor="n"
        )
        settings_frame.pack(padx=12, pady=6, fill="x")

        entries = [
            ("Pull Down (e.g. 4.5, 6.2):", "entry_down", "4.5"),
            ("Max Pull Left (e.g. 1.8, 3.0):", "entry_left", "1.8"),
            ("Max Pull Right (e.g. 1.8, 3.0):", "entry_right", "1.8"),
            ("Horizontal Sensitivity (0.1–2.0):", "entry_sensitivity", "0.5"),
        ]

        for label_text, attr, default in entries:
            tk.Label(settings_frame, text=label_text, bg="#1e1e1e", fg="white").pack(anchor="w")
            entry = tk.Entry(settings_frame, bg="white", fg="black")
            entry.insert(0, default)
            entry.pack(fill="x", pady=(2, 8))
            setattr(self, attr, entry)

        # Status
        self.status_var = tk.StringVar(
            value="Caps Lock: OFF | Anti-recoil: Inactive"
        )
        tk.Label(
            master,
            textvariable=self.status_var,
            fg="white",
            bg="#1e1e1e",
            font=("Segoe UI", 9)
        ).pack(pady=10)

        tk.Label(
            master,
            text="Controls:\n"
                 "• Caps Lock ON → anti-recoil active\n"
                 "• Caps Lock OFF → anti-recoil disabled\n"
                 "• Hold LMB + RMB → apply correction\n"
                 "• INSERT → exit program\n\n"
                 "Tip: Type name → adjust values → Save\n"
                 " or select from dropdown to load",
            justify="left",
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=6)

        # Auto-load first config if any exist
        if self.configs:
            first = list(self.configs.keys())[0]
            self.config_combo.set(first)
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, first)
            self.load_config(first)

        # Background loop
        self.running = True
        self.thread = threading.Thread(
            target=self.background_loop,
            daemon=True
        )
        self.thread.start()

        self.update_status()

    def on_closing(self):
        self.running = False
        self.master.destroy()

    def load_configs(self):
        path = os.path.join(CONFIG_DIR, CONFIG_FILE)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_configs(self):
        path = os.path.join(CONFIG_DIR, CONFIG_FILE)
        with open(path, "w") as f:
            json.dump(self.configs, f, indent=2)

    def get_current_values(self):
        try:
            down = float(self.entry_down.get())
            left = float(self.entry_left.get())
            right = float(self.entry_right.get())
            sens = float(self.entry_sensitivity.get())

            if sens < 0.05 or sens > 3.0:
                raise ValueError("Sensitivity range")

            return {
                "down": down,
                "left": left,
                "right": right,
                "sensitivity": sens
            }
        except:
            return None

    def save_config(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Please enter a config name.")
            return

        values = self.get_current_values()
        if values is None:
            messagebox.showerror(
                "Invalid input",
                "Please enter valid numbers (decimals ok)."
            )
            return

        self.configs[name] = values
        self.save_configs()

        # Refresh dropdown
        current_list = list(self.configs.keys())
        self.config_combo["values"] = current_list

        # Select the saved one
        if name in current_list:
            self.config_combo.set(name)

        messagebox.showinfo("Saved", f"Config '{name}' saved/updated.")

    def on_combo_select(self, event=None):
        name = self.config_combo.get()
        if name and name in self.configs:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)
            self.load_config(name)

    def load_config(self, name):
        if name in self.configs:
            cfg = self.configs[name]

            self.entry_down.delete(0, tk.END)
            self.entry_down.insert(0, f"{cfg['down']:.2f}")

            self.entry_left.delete(0, tk.END)
            self.entry_left.insert(0, f"{cfg['left']:.2f}")

            self.entry_right.delete(0, tk.END)
            self.entry_right.insert(0, f"{cfg['right']:.2f}")

            self.entry_sensitivity.delete(0, tk.END)
            self.entry_sensitivity.insert(0, f"{cfg['sensitivity']:.2f}")

    def background_loop(self):
        while self.running:
            if user32.GetAsyncKeyState(VK_INSERT) & 0x8000:
                self.running = False
                self.master.after(0, sys.exit)

            try:
                if user32.GetKeyState(VK_CAPITAL) & 0x0001:  # Caps on
                    if (
                        (user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
                        and (user32.GetAsyncKeyState(VK_RBUTTON) & 0x8000)
                    ):
                        values = self.get_current_values()
                        if values:
                            h_raw = random.uniform(
                                -values["left"],
                                values["right"]
                            )
                            h_move = round(h_raw * values["sensitivity"])
                            v_move = round(values["down"])

                            user32.mouse_event(
                                MOUSEEVENTF_MOVE,
                                h_move,
                                v_move,
                                0,
                                0
                            )
            except:
                pass

            time.sleep(0.007)

    def update_status(self):
        if not self.running:
            return

        active = bool(user32.GetKeyState(VK_CAPITAL) & 0x0001)

        text = (
            f"Caps Lock: {'ON ' if active else 'OFF '} | "
            f"Anti-recoil: {'Active' if active else 'Inactive'}"
        )
        self.status_var.set(text)

        self.master.after(300, self.update_status)


if __name__ == "__main__":
    root = tk.Tk()
    app = AntiRecoilApp(root)
    root.mainloop()