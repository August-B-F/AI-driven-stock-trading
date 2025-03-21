def write_to_transaction_log(text):
    with open("assets/transaction_log.txt", "r") as file:
        prev_text = file.read()
        file.close()
        
    with open("assets/transaction_log.txt", "w") as file:
        file.write(text + "\n" + prev_text)
        file.close()