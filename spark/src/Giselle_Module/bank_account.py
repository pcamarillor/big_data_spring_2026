class BankAccount:
    def __init__(self, initial_balance=0):
        self.balance = initial_balance

        self.operations = {
            "deposit": self.deposit,
            "withdraw": self.withdraw,
            "get_balance": self.get_balance,
        }

    def deposit(self, amount):
        if amount < 0:
            return "Invalid amount"
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount < 0:
            return "Invalid amount"
        if amount > self.balance:
            return "Insufficient funds"
        self.balance -= amount
        return self.balance

    def get_balance(self):
        return self.balance

    def process(self, operation_name, *args):
        if operation_name not in self.operations:
            return f"{operation_name} -> Error - Unknown operation"

        result = self.operations[operation_name](*args)
        return f"{operation_name}: {result}"
