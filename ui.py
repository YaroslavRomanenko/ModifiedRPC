import time
import tkinter as tk
import sys
import screeninfo
import pyautogui
import threading

from pypresence import Presence, exceptions
from tkinter import messagebox  

class DiscordRPCMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.width = 500
        self.height = 280
        self.center_window(self.width, self.height)
        self.resizable(False, False)
        self.title("Discord RPC Settings")
        
        self.ui_font = ("Verdana", 10)
        
        # Labels #
        self.app_id_label = tk.Label(self, font=self.ui_font, text="Application ID")
        self.details_label = tk.Label(self, font=self.ui_font, text="Details")
        self.state_label = tk.Label(self, font=self.ui_font, text="State")
        self.start_time_label = tk.Label(self, font=self.ui_font, text="Start Time (00:00:00)")
        self.large_image_key_label = tk.Label(self, font=self.ui_font, text="Large Image URL")
        self.large_text_label = tk.Label(self, font=self.ui_font, text="Large Text (for image)")
        self.small_image_key_label = tk.Label(self, font=self.ui_font, text="Small Image")
        self.small_text_label = tk.Label(self, font=self.ui_font, text="Small Text (for image)")
        
        # Entries #
        self.app_id_entry = tk.Entry(self, font=self.ui_font)
        self.details_entry = tk.Entry(self, font=self.ui_font)
        self.state_entry = tk.Entry(self, font=self.ui_font)
        self.start_time_entry = tk.Entry(self, font=self.ui_font)
        self.large_image_key_entry = tk.Entry(self, font=self.ui_font)
        self.large_text_entry = tk.Entry(self, font=self.ui_font)
        self.small_image_key_entry = tk.Entry(self, font=self.ui_font)
        self.small_text_entry = tk.Entry(self, font=self.ui_font)
        
        # Button #
        self.start_button = tk.Button(self, width=12, font=self.ui_font, text="Start", command=self.start_setting_rpc_thread)
        self.stop_button = tk.Button(self, width=12, font=self.ui_font, text="Stop", command=self.stop_rpc, state=tk.DISABLED)
        
        self.app_id_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.app_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.details_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.details_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.state_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.state_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.large_image_key_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.large_image_key_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        self.large_text_label.grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.large_text_entry.grid(row=4, column=1, padx=5, pady=2, sticky="ew")
        self.small_image_key_label.grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.small_image_key_entry.grid(row=5, column=1, padx=5, pady=2, sticky="ew")
        self.small_text_label.grid(row=6, column=0, padx=5, pady=2, sticky="w")
        self.small_text_entry.grid(row=6, column=1, padx=5, pady=2, sticky="ew")

        self.start_button.grid(row=7, column=0, padx=5, pady=10)
        self.stop_button.grid(row=7, column=1, padx=5, pady=10, sticky="w")

        self.columnconfigure(1, weight=1)
        
        self.RPC = None
        self.rpc_thread = None
        self.stop_event = threading.Event()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self, width, height):
        """Centers a window on the primary monitor"""
        try:
            monitors = screeninfo.get_monitors()
            primary_monitor = next((m for m in monitors if m.is_primary), None)
            
            if primary_monitor:
                pm_width, pm_height = primary_monitor.width, primary_monitor.height
                pm_x, pm_y = primary_monitor.x, primary_monitor.y
                x = pm_x + (pm_width - width) // 2
                y = pm_y + (pm_height - height) // 2
                x, y = max(pm_x, x), max(pm_y, y)
                
                print(f"Centering on primary: {width}x{height}+{x}+{y}")
                self.geometry(f"{width}x{height}+{x}+{y}")
            else:
                print("Warning: Primary monitor not found")
                screen_width, screen_height = pyautogui.size()
                
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
                
        except Exception as e:
            print(f"Error centering window: {e}. Using basic Tkinter placement")
            
    def update_status(self, text, color="black"):
        self.status_label.config(text=f"Status: {text}", fg=color)
            
    def start_setting_rpc_thread(self):
        if self.rpc_thread and self.rpc_thread.is_alive():
            messagebox.showwarning("Warining", "RPC is already launched")
            return
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.stop_event.clear()
        self.rpc_thread = threading.Thread(target=self.set_rpc, daemon=True)
        self.rpc_thread.start()
        
    
    def stop_rpc(self):
        if self.rpc_thread and self.rpc_thread.is_alive():
            self.stop_event.set()
            print("Signaled RPC thread to stop")
        
        if self.RPC:
            try:
                self.RPC.close()
                print("RPC connection closed by stop button")
                self.RPC = None
            except Exception as e:
                print(f"Error closing RPC on stop: {e}")
                
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.rpc_thread = None
           
    def set_rpc(self):
        client_id = self.app_id_entry.get()
        if not client_id:
            self.after(0, lambda: messagebox.showerror(message="Please, enter Application ID"))
            self.after(0 , self.stop_rpc)
            return
        
        try:
            RPC = Presence(client_id)
            RPC.connect()
            print("Successfully connected to Discord RPC!")
            
        except exceptions.DiscordNotFound:
            self.after(0, lambda: messagebox.showerror(message="Error: Discord not launched. Please, launch Discord and try again"))
            self.after(0 , self.stop_rpc)
            return
        except Exception as e:
            print(f"The error has occured during connection: {e}")
            self.after(0, lambda: messagebox.showerror(message=f"Error during connection"))
            self.after(0, self.stop_rpc)
            return
        
        start_time = int(time.time())
        
        print("Updating presence...")
        try:
            RPC.update (
                details=self.details_entry.get() or None,
                state=self.state_entry.get() or None,
                start=start_time,
                large_image=self.large_image_key_entry.get() or None,
                large_text=self.large_text_entry.get() or None,
                small_image=self.small_image_key_entry.get() or None,
                small_text=self.small_text_entry.get() or None
            )
            
            print("Presence updated successfully")
        except Exception as e:
            print(f"Error during updating status: {e}")
            self.after(0, lambda: messagebox.showerror(message=f"Error during updating the status"))
            if self.RPC:
                self.RPC.close()
            self.after(0, self.stop_rpc)
            return
            
        print("Presence is active")
        while not self.stop_event.is_set():
            try:
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in RPC loop: {e}")
                break
        
        print("RPC thread loop finished")
    
    def on_closing(self):
        print("Closing application...")
        self.stop_rpc()
        self.destroy()