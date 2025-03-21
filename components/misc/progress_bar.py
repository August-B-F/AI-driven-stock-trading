import time 
import os

def print_progress_bar(iteration, total, decimals = 1, length = 100, fill = "█", description = "Progress: "):
    time.sleep(0.1)
    os.system("cls" if os.name == "nt" else "clear")
    print(description)
    
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    
    print(f"\rProgress: |{bar}| {percent}%", end = "\r")
    
    if iteration == total: 
        print()