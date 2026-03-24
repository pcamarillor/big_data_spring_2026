class BankAccount:
    def __init__(self, initial_balance=0):
        self.balance = initial_balance

        self.operations = {
            "deposit": self.deposit,
            "withdraw": self.withdraw,
            "get_balance": self.get_balance
        }

    def deposit(self, amount):
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative")
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount < 0:
            raise ValueError("Withdraw amount cannot be negative")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance

    def get_balance(self):
        return self.balance

    def process(self, operation_name, *args):
        if operation_name not in self.operations:
            raise ValueError(f"Operation '{operation_name}' not supported")
        return self.operations[operation_name](*args)