def write_to_prediction_log(text):
    with open("assets/predictions_log.txt", "r") as file:
        prev_text = file.read()
        file.close()
        
    with open("assets/predictions_log.txt", "w") as file:
        file.write(text + "\n" + prev_text)
        file.close()