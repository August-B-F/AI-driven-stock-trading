def write_to_log(text):
    with open("assets/log.txt", "r") as file:
        prev_text = file.read()
        file.close()
        
    with open("assets/log.txt", "w") as file:
        file.write(text + "\n" + prev_text)
        file.close()