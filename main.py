import tkinter as tk
from tkinter import ttk
from pynput.mouse import Button, Controller as MouseController, Listener as MouseListener
from pynput.keyboard import KeyCode, Key, Listener as KeyboardListener
from threading import Thread, Event
import time
import random
import sv_ttk

class AutoClickerGUI:
    def __init__(self):
        self.root = tk.Tk()
        sv_ttk.set_theme("light")
        self.root.resizable(False, False)
        self.root.title("KidEater2000")

        self.mouse = MouseController()
        
        self.left_clicking = False
        self.right_clicking = False
        self.cps_left = tk.IntVar(value=10)
        self.cps_right = tk.IntVar(value=10)
        self.blatant_var_left = tk.BooleanVar(value=False)
        self.blatant_var_right = tk.BooleanVar(value=False)
        self.hold_mode_left = tk.BooleanVar(value=True) 
        self.hold_mode_right = tk.BooleanVar(value=True)
        self.ignore_next = False
        
        self.left_trigger_key = Button.x2
        self.right_trigger_key = Button.x1
        self.quit_key = Key.f7
        
        self.key_recording_mode = False
        self.recorded_key = None
        
        self.setup_gui()
        self.start_threads()

    def setup_gui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.setup_left_click_tab(notebook)
        self.setup_right_click_tab(notebook)
        self.setup_misc_tab(notebook)
        

    def setup_left_click_tab(self, notebook):
        lmb_frame = ttk.Frame(notebook)
        notebook.add(lmb_frame, text='Left Click')
        self.setup_key_binding(lmb_frame, "left", self.left_trigger_key)
        self.setup_cps_control(lmb_frame, self.cps_left, self.blatant_var_left)
        self.setup_hold_mode_checkbox(lmb_frame, self.hold_mode_left)  
        
    def setup_right_click_tab(self, notebook):
        rmb_frame = ttk.Frame(notebook)
        notebook.add(rmb_frame, text='Right Click')
        self.setup_key_binding(rmb_frame, "right", self.right_trigger_key)
        self.setup_cps_control(rmb_frame, self.cps_right, self.blatant_var_right)
        self.setup_hold_mode_checkbox(rmb_frame, self.hold_mode_right)  
        

    def setup_misc_tab(self, notebook):
        misc_frame = ttk.Frame(notebook)
        notebook.add(misc_frame, text='Misc')
        
        self.setup_quit_key_binding(misc_frame)

    def setup_cps_control(self, parent_frame, cps_var, blatant_var):
        cps_frame = ttk.Frame(parent_frame)
        cps_frame.pack(pady=(0, 10), padx=10, fill='x')
        
        cps_label = ttk.Label(cps_frame, text="CPS: ")
        cps_label.pack(side='left')
        
        cps_value_label = ttk.Label(cps_frame, textvariable=cps_var, width=3)
        cps_value_label.pack(side='left', padx=(0, 10))
        
        cps_slider = ttk.Scale(
            cps_frame,
            from_=1,
            to=20,
            variable=cps_var,
            orient='horizontal',
            command=lambda val: cps_var.set(round(float(val)))
        )
        cps_slider.pack(side='left', fill='x', expand=True)
        self.setup_blatant_checkbox(parent_frame,cps_slider,blatant_var,cps_var)

    def setup_blatant_checkbox(self, parent_frame, cps_slider, blatant_var,cps_var):
        cps_frame = ttk.Frame(parent_frame)
        cps_frame.pack(fill='x')
        blatant_checkbox = ttk.Checkbutton(
            cps_frame,
            text="Blatant",
            variable=blatant_var,
            command=lambda: self.toggle_blatant_mode(blatant_var, cps_slider,cps_var)
        )
        blatant_checkbox.pack(side='left', padx=(5, 0), pady=(0,10))

    def toggle_blatant_mode(self,blatant_var,cps_slider,cps_var):
        if blatant_var.get():
            cps_slider.configure(to=60)
            if cps_var.get()>20:
                cps_var.set(20)
        else:
            cps_slider.configure(to=20)
            if cps_var.get()>20:
                cps_var.set(20)

    def setup_hold_mode_checkbox(self, parent_frame, hold_var):
        hold_frame = ttk.Frame(parent_frame)
        hold_frame.pack(fill='x')
        hold_checkbox = ttk.Checkbutton(
            hold_frame,
            text="Hold",
            variable=hold_var
        )
        hold_checkbox.pack(side='left', padx=(5, 0), pady=(0,10))

    def setup_key_binding(self, parent_frame, key_type, current_key):
        key_frame = ttk.Frame(parent_frame)
        key_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Label(key_frame, text="Trigger:").pack(side='left')
        key_label = ttk.Label(key_frame, text=self.format_key(current_key))
        key_label.pack(side='left', padx=5)
        ttk.Button(key_frame, text="Change Bind", command=lambda: self.start_recording(key_type, key_label)).pack(side='left', padx=5)

    def setup_quit_key_binding(self, parent_frame):
        quit_frame = ttk.Frame(parent_frame)
        quit_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Label(quit_frame, text="Quit:").pack(side='left')
        self.quit_key_label = ttk.Label(quit_frame, text=self.format_key(self.quit_key))
        self.quit_key_label.pack(side='left', padx=5)
        ttk.Button(quit_frame, text="Change Bind", command=lambda: self.start_recording("quit", self.quit_key_label)).pack(side='left', padx=5)

    def start_threads(self):
        Thread(target=self.left_click_spam, daemon=True).start()
        Thread(target=self.right_click_spam, daemon=True).start()
        Thread(target=self.check_input, daemon=True).start()

    def format_key(self, key):
        if isinstance(key, Key):
            return f"Key.{key.name}"
        elif isinstance(key, KeyCode):
            return key.char if key.char else f"KeyCode({key.vk})"
        return str(key)

    def left_click_spam(self):
        while True:
            if self.left_clicking and not self.key_recording_mode:
                self.click(Button.left, self.cps_left)
            else:
                time.sleep(0.01)

    def right_click_spam(self):
        while True:
            if self.right_clicking and not self.key_recording_mode:
                self.click(Button.right, self.cps_right)
            else:
                time.sleep(0.01)

    def click(self, button, cps_var):
        try:
            cps = int(cps_var.get())
            if cps <= 0:
                raise ValueError
            delay = 1 / cps
            self.mouse.click(button)
            time.sleep(max(0.01, delay))
        except ValueError:
            time.sleep(0.1)

    def keys_match(self, key1, key2):
        if isinstance(key1, Key) and isinstance(key2, Key):
            return key1 == key2
        elif isinstance(key1, KeyCode) and isinstance(key2, KeyCode):
            return (key1.char and key1.char == key2.char) or (key1.vk == key2.vk)
        return str(key1) == str(key2)

    def check_input(self):
        def on_press(key):
            if self.key_recording_mode:
                return True

            try:
                if self.keys_match(key, self.left_trigger_key):
                    if self.hold_mode_left.get() and not self.ignore_next:
                        self.left_clicking = True
                elif self.keys_match(key, self.right_trigger_key):
                    if self.hold_mode_right.get() and not self.ignore_next:
                        self.right_clicking = True
                elif self.keys_match(key, self.quit_key):
                    self.root.after(0, self.root.quit)
            except Exception:
                pass
            return True

        def on_release(key):
            try:
                if self.keys_match(key, self.left_trigger_key):
                    if self.ignore_next:
                        self.ignore_next = False
                    elif self.hold_mode_left.get():
                        self.left_clicking = False
                    else:
                        self.left_clicking = not self.left_clicking
                elif self.keys_match(key, self.right_trigger_key):
                    if self.ignore_next:
                        self.ignore_next = False
                    elif self.hold_mode_right.get():
                        self.right_clicking = False
                    else:
                        self.right_clicking = not self.right_clicking
            except Exception:
                pass
            return True
        
        def on_click(x, y, button, pressed):
            if self.key_recording_mode:
                return True

            try:
                if pressed:
                    if self.keys_match(button, self.left_trigger_key):
                        if self.hold_mode_left.get() and not self.ignore_next:
                            self.left_clicking = True
                    elif self.keys_match(button, self.right_trigger_key):
                        if self.hold_mode_right.get() and not self.ignore_next:
                            self.right_clicking = True
                    elif self.keys_match(button, self.quit_key):
                        self.root.after(0, self.root.quit)
                else:  # Released
                    if self.keys_match(button, self.left_trigger_key):
                        if self.ignore_next:
                            self.ignore_next = False
                        elif self.hold_mode_left.get():
                            self.left_clicking = False
                        else:
                            self.left_clicking = not self.left_clicking
                    elif self.keys_match(button, self.right_trigger_key):
                        if self.ignore_next:
                            self.ignore_next = False
                        elif self.hold_mode_right.get():
                            self.right_clicking = False
                        else:
                            self.right_clicking = not self.right_clicking
            except Exception:
                pass
            return True

        with KeyboardListener(on_press=on_press, on_release=on_release) as k_listener:
            with MouseListener(on_click=on_click) as m_listener:
                k_listener.join()
                m_listener.join()

    

    def start_recording(self, key_type, key_label):
        if self.key_recording_mode:
            return

        self.key_recording_mode = True
        self.recorded_key = None
        stop_event = Event()  

        def on_press(key):
            self.recorded_key = key
            stop_event.set() 

        def on_click(x, y, button, pressed):
            self.recorded_key = button
            stop_event.set()  

        def recording_complete():
            if self.recorded_key:
                if key_type == "left":
                    self.left_trigger_key = self.recorded_key
                    self.ignore_next = True  # Set flag when binding changes
                elif key_type == "right":
                    self.right_trigger_key = self.recorded_key
                    self.ignore_next = True  # Set flag when binding changes
                elif key_type == "quit":
                    self.quit_key = self.recorded_key

                key_label.config(text=self.format_key(self.recorded_key))

            self.key_recording_mode = False
        Thread(
            target=lambda: self.record_key(on_press, on_click, recording_complete, stop_event),
            daemon=True
        ).start()

    def record_key(self, on_press, on_click, recording_complete, stop_event):
        # Start both listeners
        with KeyboardListener(on_press=on_press) as rk_listener, MouseListener(on_click=on_click) as rm_listener:
            stop_event.wait()
            rk_listener.stop()
            rm_listener.stop()
        self.root.after(0, recording_complete)


    def run(self):
        self.root.mainloop()

def main():
    app = AutoClickerGUI()
    app.run()

if __name__ == "__main__":
    main()