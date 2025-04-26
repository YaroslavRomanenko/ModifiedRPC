import time
import tkinter as tk
import tkinter.constants as tk_constants
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
        self.height = 300
        self.center_window(self.width, self.height)
        self.resizable(False, False)
        self.title("Discord RPC Settings")

        self.ui_font = ("Verdana", 10)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Вирізати", command=self._entry_cut)
        self.context_menu.add_command(label="Копіювати", command=self._entry_copy)
        self.context_menu.add_command(label="Вставити", command=self._entry_paste)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Виділити все", command=self._entry_select_all)
        self._context_menu_target = None

        self.app_id_label = tk.Label(self, font=self.ui_font, text="Application ID")
        self.details_label = tk.Label(self, font=self.ui_font, text="Details")
        self.state_label = tk.Label(self, font=self.ui_font, text="State")
        self.large_image_key_label = tk.Label(self, font=self.ui_font, text="Large Image URL/Key")
        self.large_text_label = tk.Label(self, font=self.ui_font, text="Large Text (for image)")
        self.small_image_key_label = tk.Label(self, font=self.ui_font, text="Small Image URL/Key")
        self.small_text_label = tk.Label(self, font=self.ui_font, text="Small Text (for image)")

        self.app_id_entry = tk.Entry(self, font=self.ui_font)
        self.details_entry = tk.Entry(self, font=self.ui_font)
        self.state_entry = tk.Entry(self, font=self.ui_font)
        self.large_image_key_entry = tk.Entry(self, font=self.ui_font)
        self.large_text_entry = tk.Entry(self, font=self.ui_font)
        self.small_image_key_entry = tk.Entry(self, font=self.ui_font)
        self.small_text_entry = tk.Entry(self, font=self.ui_font)

        self.entry_widgets = [
            self.app_id_entry, self.details_entry, self.state_entry,
            self.large_image_key_entry, self.large_text_entry,
            self.small_image_key_entry, self.small_text_entry
        ]

        for entry in self.entry_widgets:
            entry.bind("<Button-3>", self._show_context_menu)
            entry.bind("<Control-a>", self._entry_select_all_event)
            entry.bind("<Control-A>", self._entry_select_all_event)
            entry.bind("<Control-c>", self._entry_copy_event)
            entry.bind("<Control-C>", self._entry_copy_event)
            entry.bind("<Control-x>", self._entry_cut_event)
            entry.bind("<Control-X>", self._entry_cut_event)
            entry.bind("<Control-v>", self._entry_paste_event)
            entry.bind("<Control-V>", self._entry_paste_event)
            entry.bind("<FocusOut>", self._entry_deselect_on_focus_out)

        self.start_button = tk.Button(self, width=12, font=self.ui_font, text="Start", command=self.start_setting_rpc_thread)
        self.stop_button = tk.Button(self, width=12, font=self.ui_font, text="Stop", command=self.stop_rpc, state=tk.DISABLED)

        self.app_id_label.grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.app_id_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        self.details_label.grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.details_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")
        self.state_label.grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.state_entry.grid(row=2, column=1, padx=5, pady=3, sticky="ew")
        self.large_image_key_label.grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.large_image_key_entry.grid(row=3, column=1, padx=5, pady=3, sticky="ew")
        self.large_text_label.grid(row=4, column=0, padx=5, pady=3, sticky="w")
        self.large_text_entry.grid(row=4, column=1, padx=5, pady=3, sticky="ew")
        self.small_image_key_label.grid(row=5, column=0, padx=5, pady=3, sticky="w")
        self.small_image_key_entry.grid(row=5, column=1, padx=5, pady=3, sticky="ew")
        self.small_text_label.grid(row=6, column=0, padx=5, pady=3, sticky="w")
        self.small_text_entry.grid(row=6, column=1, padx=5, pady=3, sticky="ew")

        self.start_button.grid(row=7, column=0, padx=5, pady=15)
        self.stop_button.grid(row=7, column=1, padx=5, pady=15, sticky="w")

        self.columnconfigure(1, weight=1)

        self.RPC = None
        self.rpc_thread = None
        self.stop_event = threading.Event()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _show_context_menu(self, event):
        self._context_menu_target = event.widget
        if not isinstance(self._context_menu_target, tk.Entry):
             return

        has_selection = False
        try:
            if self._context_menu_target.selection_present():
                has_selection = True
        except tk.TclError:
            pass

        has_text = bool(self._context_menu_target.get())
        clipboard_content = ""
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            pass

        self.context_menu.entryconfigure("Вирізати", state=tk_constants.NORMAL if has_selection else tk_constants.DISABLED)
        self.context_menu.entryconfigure("Копіювати", state=tk_constants.NORMAL if has_selection else tk_constants.DISABLED)
        self.context_menu.entryconfigure("Вставити", state=tk_constants.NORMAL if clipboard_content else tk_constants.DISABLED)
        self.context_menu.entryconfigure("Виділити все", state=tk_constants.NORMAL if has_text else tk_constants.DISABLED)

        self.context_menu.tk_popup(event.x_root, event.y_root)
        
    def _entry_cut(self, widget=None):
        target = widget or self._context_menu_target
        if target and isinstance(target, tk.Entry):
            try:
                if target.selection_present():
                    text = target.selection_get()
                    self.clipboard_clear()
                    self.clipboard_append(text)
                    target.delete(tk_constants.SEL_FIRST, tk_constants.SEL_LAST)
            except tk.TclError:
                 print("Error cutting text (no selection?)")
                 
    def _entry_copy(self, widget=None):
        target = widget or self._context_menu_target
        if target and isinstance(target, tk.Entry):
            try:
                if target.selection_present():
                    text = target.selection_get()
                    self.clipboard_clear()
                    self.clipboard_append(text)
            except tk.TclError:
                 print("Error copying text (no selection?)")
                 
    def _entry_paste(self, widget=None):
        target = widget or self._context_menu_target
        if target and isinstance(target, tk.Entry):
            try:
                text = self.clipboard_get()
                if target.selection_present():
                     target.delete(tk_constants.SEL_FIRST, tk_constants.SEL_LAST)
                target.insert(tk_constants.INSERT, text)
            except tk.TclError:
                print("Clipboard empty or does not contain text.")
                
    def _entry_select_all(self, widget=None):
        target = widget or self._context_menu_target
        if target and isinstance(target, tk.Entry):
            target.select_range(0, tk_constants.END)
            target.icursor(tk_constants.END)

    def _entry_deselect_on_focus_out(self, event):
        widget = event.widget
        if isinstance(widget, tk.Entry):
            try:
                if widget.selection_present():
                    widget.select_clear()
            except tk.TclError:
                pass

    def _entry_cut_event(self, event):
        if isinstance(event.widget, tk.Entry):
            self._entry_cut(event.widget)
            return "break"

    def _entry_copy_event(self, event):
        if isinstance(event.widget, tk.Entry):
            self._entry_copy(event.widget)
            return "break"

    def _entry_paste_event(self, event):
        if isinstance(event.widget, tk.Entry):
            self._entry_paste(event.widget)
            return "break"

    def _entry_select_all_event(self, event):
        if isinstance(event.widget, tk.Entry):
            self._entry_select_all(event.widget)
            return "break"

    def center_window(self, width, height):
        try:
            monitors = screeninfo.get_monitors()
            primary_monitor = next((m for m in monitors if m.is_primary), None)

            if primary_monitor:
                pm_width, pm_height = primary_monitor.width, primary_monitor.height
                pm_x, pm_y = primary_monitor.x, primary_monitor.y
                x = pm_x + (pm_width - width) // 2
                y = pm_y + (pm_height - height) // 2
                x, y = max(pm_x, x), max(pm_y, y)
                self.geometry(f"{width}x{height}+{x}+{y}")
            else:
                print("Warning: Primary monitor not found, using pyautogui")
                screen_width, screen_height = pyautogui.size()
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
        except Exception as e:
            print(f"Error centering window: {e}. Using basic Tkinter placement")
            self.eval('tk::PlaceWindow . center')
            
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