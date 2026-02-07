class BankAccount:

    def __init__(self, balance):
        self.balance = balance
        self.operations = {
            "deposit": self.deposit,
            "withdraw": self.withdraw,
            "get_balance": self.get_balance
        }

    def process(self, operation, amount=0):
        if operation in self.operations:
            return self.operations[operation](amount)
        else:
            raise ValueError("Invalid operation")

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount

    def get_balance(self, amount):
        print(self.balance)
