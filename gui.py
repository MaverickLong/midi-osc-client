import tkinter as tk
from tkinter import ttk
import sv_ttk

import darkdetect
import queue
import mido
import mido.backends.rtmidi

from ctypes import windll
windll.shcore.SetProcessDpiAwareness(1)

from pythonosc.udp_client import SimpleUDPClient
from utils import load_config, save_config, dummy_in, dummy_out, send_osc


class AppModel:
    def __init__(self):
        self.config = load_config()
        self.input_devices = mido.get_input_names() + ["None (disabled)"]
        self.output_devices = mido.get_output_names() + ["None (disabled)"]
        self.status_messages = []


class AppView:
    def __init__(self, root):
        self.root = root
        root.title("MIDI OSC Controller")

        root.geometry("1200x600")
        root.resizable(0, 0)

        frame = ttk.Frame(root)
        frame.pack(side="top", fill='x')
        frame.grid_columnconfigure(0, weight=1, uniform="group1")
        frame.grid_columnconfigure(1, weight=1, uniform="group1")

        # MIDI Input selector
        tk.Label(frame, text="MIDI Input Device:").grid(row = 0, column = 0, sticky='we')
        self.in_device_cb = ttk.Combobox(frame, state="readonly")
        self.in_device_cb.grid(row = 1, column = 0)

        # MIDI Output selector
        tk.Label(frame, text="MIDI Output Device:").grid(row = 0, column = 1, sticky='we')
        self.out_device_cb = ttk.Combobox(frame, state="readonly")
        self.out_device_cb.grid(row = 1, column = 1)

        # Status display
        tk.Label(root, text="MIDI Messages:").pack()
        
        self.status_text = tk.Text(root, height=15, width=100)
        self.status_text.pack()
        self.status_text.config(state=tk.DISABLED)


class AppController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.queue = queue.Queue()

        self.view.in_device_cb['values'] = self.model.input_devices
        self.view.out_device_cb['values'] = self.model.output_devices

        self.view.in_device_cb.set(self.model.config.get("midi_in_device", "None (disabled)"))
        self.view.out_device_cb.set(self.model.config.get("midi_out_device", "None (disabled)"))

        self.view.in_device_cb.bind("<<ComboboxSelected>>", self.apply_devices)
        self.view.out_device_cb.bind("<<ComboboxSelected>>", self.apply_devices)

        self.view.root.after(100, self.update_gui_from_queue)

        self.start_dispatch_thread()

    def apply_devices(self, event):
        self.model.config["midi_in_device"] = self.view.in_device_cb.get()
        self.model.config["midi_out_device"] = self.view.out_device_cb.get()
        save_config(self.model.config)
        self.restart_dispatch_thread()

    def on_midi_message(self, msg):
        self.queue.put(str(msg))
        self.out_device.send(msg)
        send_osc(msg, self.client)

    def start_dispatch_thread(self):
        self.midi_queue = queue.Queue()
        try:
            in_dev_name = self.model.config.get("midi_in_device")
            out_dev_name = self.model.config.get("midi_out_device")

            self.client = SimpleUDPClient(self.model.config["vrchat_receive_address"],
                                        self.model.config["vrchat_receive_port"])
            self.in_device = dummy_in() if in_dev_name not in mido.get_input_names() else mido.open_input(in_dev_name, callback=self.on_midi_message)
            self.out_device = dummy_out() if out_dev_name not in mido.get_output_names() else mido.open_output(out_dev_name)
            
        except Exception as e:
            self.queue.put(f"[ERROR] {e}")

    def stop_dispatch_thread(self):
        try:
            if hasattr(self, 'in_device'):
                self.in_device.close()
            if hasattr(self, 'out_device'):
                self.out_device.close()
        except Exception:
            pass

    def restart_dispatch_thread(self):
        self.stop_dispatch_thread()
        self.start_dispatch_thread()

    def update_gui_from_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                self.view.status_text.config(state=tk.NORMAL)
                self.view.status_text.insert(tk.END, msg + "\n")
                self.view.status_text.config(state=tk.DISABLED)
                self.view.status_text.see(tk.END)
        except queue.Empty:
            pass
        self.view.root.after(100, self.update_gui_from_queue)


if __name__ == "__main__":
    root = tk.Tk()
    model = AppModel()
    view = AppView(root)
    controller = AppController(model, view)
    sv_ttk.set_theme(darkdetect.theme())
    root.mainloop()