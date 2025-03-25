import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from screeninfo import get_monitors
import uuid

# Dictionary to store progress windows, using unique IDs as keys
progress_windows = {}

class ProgressWindow:
    def __init__(self, total, description="Progress: ", decimals=1, length=300, theme='arc'):
        self.total = total
        self.description = description
        self.decimals = decimals
        self.length = length
        
        self.root = ThemedTk(theme=theme)
        self.root.title("Progress")
        
        monitors = get_monitors()
        
        if len(monitors) > 1:
            second_monitor = monitors[1]
            x = second_monitor.x + 300
            y = second_monitor.y + 500
            
        else:
            x = 300
            y = 500
            
        self.root.geometry(f"400x150+{x}+{y}")

        self.label = ttk.Label(self.root, text=description, font=("Arial", 14, "bold"), foreground="blue")
        self.label.pack(pady=20)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=length, mode="determinate")
        self.progress.pack(pady=10)
        self.progress["maximum"] = total

        self.percent_label = ttk.Label(self.root, text="0.0%", font=("Arial", 12), foreground="green")
        self.percent_label.pack(pady=10)

        self.root.update()

    def update_progress(self, iteration):
        self.progress["value"] = iteration
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (iteration / float(self.total)))
        self.percent_label.config(text=f"{percent}%")
        self.root.update()

    def close(self):
        self.root.destroy()

def print_progress_bar(iteration, total, decimals=1, length=100, fill="█", description="Progress: "):
    global progress_windows
    current_id = getattr(print_progress_bar, '_current_id', None)
    
    if current_id is None or iteration == 0:
        current_id = str(uuid.uuid4())  
        print_progress_bar._current_id = current_id
        progress_windows[current_id] = ProgressWindow(total, description, decimals, length * 3, theme='arc')
    
    window = progress_windows[current_id]
    window.update_progress(iteration)
    
    if iteration == total:
        window.close()
        del progress_windows[current_id]

        if hasattr(print_progress_bar, '_current_id'):
            delattr(print_progress_bar, '_current_id')
            
            
            
# import time 
# import os

# def print_progress_bar(iteration, total, decimals = 1, length = 100, fill = "█", description = "Progress: "):
#     time.sleep(0.1)
#     os.system("cls" if os.name == "nt" else "clear")
#     print(description)
    
#     percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
#     filledLength = int(length * iteration // total)
#     bar = fill * filledLength + "-" * (length - filledLength)
    
#     print(f"\rProgress: |{bar}| {percent}%", end = "\r")
    
#     if iteration == total: 
#         print()