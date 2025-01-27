import tkinter as tk
from tkinter import ttk
from pynput.mouse import Button, Controller, Listener as MouseListener
from pynput.keyboard import Key, KeyCode, Listener as KeyboardListener
from threading import Thread, Lock
import time
import sv_ttk

class AutoClicker:
    def __init__(self):
        self.mouse = Controller()
        self.lock = Lock()
        self.running = True
        self.state = {'left': {'active': False, 'cps': 10, 'blatant': False, 'hold': True, 'key': Button.x2},
                     'right': {'active': False, 'cps': 10, 'blatant': False, 'hold': True, 'key': Button.x1}}
        self.quit_key = Key.f7
        self.recording_state = {'active': False, 'target': None}
        self.setup_gui()
        Thread(target=self.input_thread, daemon=True).start()
        Thread(target=lambda: self.click_thread('left'), daemon=True).start()
        Thread(target=lambda: self.click_thread('right'), daemon=True).start()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("AutoClicker")
        self.root.resizable(False, False)
        sv_ttk.set_theme("light")
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        self.tabs = {button_type: self.create_click_tab(notebook, button_type) for button_type in ['left', 'right']}
        misc_frame = ttk.Frame(notebook)
        notebook.add(misc_frame, text='Misc')
        self.setup_quit_binding(misc_frame)

    def create_click_tab(self, notebook, button_type):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=f'{button_type.title()} Click')
        bind_frame = ttk.Frame(frame)
        bind_frame.pack(pady=10, padx=10, fill='x')
        ttk.Label(bind_frame, text="Trigger:").pack(side='left')
        key_label = ttk.Label(bind_frame, text=str(self.state[button_type]['key']))
        key_label.pack(side='left', padx=5)
        ttk.Button(bind_frame, text="Change Bind", command=lambda: self.record_key(button_type, key_label)).pack(side='left', padx=5)
        cps_frame = ttk.Frame(frame)
        cps_frame.pack(pady=(0, 10), padx=10, fill='x')
        ttk.Label(cps_frame, text="CPS:").pack(side='left')
        cps_var = tk.IntVar(value=self.state[button_type]['cps'])
        cps_label = ttk.Label(cps_frame, textvariable=cps_var, width=3)
        cps_label.pack(side='left', padx=(0, 10))
        slider = ttk.Scale(cps_frame, from_=1, to=20, variable=cps_var, orient='horizontal',
                         command=lambda val: self.update_cps(button_type, val))
        slider.pack(side='left', fill='x', expand=True)
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', padx=5)
        blatant_var = tk.BooleanVar(value=self.state[button_type]['blatant'])
        hold_var = tk.BooleanVar(value=self.state[button_type]['hold'])
        ttk.Checkbutton(control_frame, text="Blatant", variable=blatant_var,
                       command=lambda: self.toggle_blatant(button_type, slider, blatant_var)).pack(side='left', pady=(0, 10))
        ttk.Checkbutton(control_frame, text="Hold", variable=hold_var,
                       command=lambda: self.toggle_hold(button_type, hold_var)).pack(side='left', padx=10, pady=(0, 10))
        return frame

    def setup_quit_binding(self, frame):
        quit_frame = ttk.Frame(frame)
        quit_frame.pack(pady=10, padx=10, fill='x')
        ttk.Label(quit_frame, text="Quit:").pack(side='left')
        self.quit_label = ttk.Label(quit_frame, text=str(self.quit_key))
        self.quit_label.pack(side='left', padx=5)
        ttk.Button(quit_frame, text="Change Bind", command=lambda: self.record_key('quit', self.quit_label)).pack(side='left', padx=5)

    def update_cps(self, button_type, value):
        with self.lock: self.state[button_type]['cps'] = int(float(value))

    def toggle_blatant(self, button_type, slider, blatant_var):
        with self.lock:
            self.state[button_type]['blatant'] = blatant_var.get()
            slider.configure(to=60 if self.state[button_type]['blatant'] else 20)
            if self.state[button_type]['cps'] > 20 and not self.state[button_type]['blatant']:
                self.state[button_type]['cps'] = 20

    def toggle_hold(self, button_type, hold_var):
        with self.lock: self.state[button_type]['hold'] = hold_var.get()

    def record_key(self, target, label):
        if self.recording_state['active']: return
        self.recording_state.update({'active': True, 'target': target})
        def on_input(key):
            if not self.recording_state['active']: return False
            with self.lock:
                if self.recording_state['target'] == 'quit': self.quit_key = key
                else: self.state[self.recording_state['target']]['key'] = key
                label.config(text=str(key))
                self.recording_state['active'] = False
                return False
        Thread(target=lambda: self.start_recording(on_input), daemon=True).start()

    def start_recording(self, callback):
        with KeyboardListener(on_press=callback) as keyboard_listener, \
             MouseListener(on_click=lambda x,y,button,pressed: callback(button) if pressed else None) as mouse_listener:
            keyboard_listener.join()
            mouse_listener.join()

    def click_thread(self, button_type):
        button = Button.left if button_type == 'left' else Button.right
        while self.running:
            if self.state[button_type]['active'] and not self.recording_state['active']:
                try:
                    clicks_per_second = self.state[button_type]['cps']
                    if clicks_per_second > 0:
                        self.mouse.click(button)
                        time.sleep(1/clicks_per_second)
                    else: time.sleep(0.01)
                except: time.sleep(0.01)
            else: time.sleep(0.01)

    def input_thread(self):
        def handle_key(key, pressed):
            if self.recording_state['active']: return True
            try:
                if str(key) == str(self.quit_key) and pressed:
                    self.running = False
                    self.root.quit()
                    return False
                for button_type in ['left', 'right']:
                    if str(key) == str(self.state[button_type]['key']):
                        with self.lock:
                            if pressed:
                                if self.state[button_type]['hold']: self.state[button_type]['active'] = True
                            else:
                                if self.state[button_type]['hold']: self.state[button_type]['active'] = False
                                else: self.state[button_type]['active'] = not self.state[button_type]['active']
            except: pass
            return True
        with KeyboardListener(on_press=lambda k: handle_key(k, True),
                            on_release=lambda k: handle_key(k, False)) as keyboard_listener, \
             MouseListener(on_click=lambda x,y,b,p: handle_key(b, p)) as mouse_listener:
            keyboard_listener.join()
            mouse_listener.join()

    def run(self): self.root.mainloop()

if __name__ == "__main__":
    AutoClicker().run()