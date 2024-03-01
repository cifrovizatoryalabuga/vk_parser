with open("accounts.txt", "r") as file:
    messages = file.readlines()
    
print(messages[0].split(':'))