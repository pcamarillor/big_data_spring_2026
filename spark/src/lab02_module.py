class BankAccount:
    def __init__(self, balance):
        self.balance = balance

    def process(self, action, amount):
        if (action == "deposit"):
            self.balance += amount
            print("Deposit Successful.\n   New Balance:", self.balance)
        elif (action == "withdraw"):
            self.balance -= amount
            print("Withdrawal Successful.\n   New Balance:", self.balance)
        else:
            raise ValueError("Invalid Action. Try again...")