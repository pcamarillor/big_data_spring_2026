class BankAccount():
    def deposit(self, qty):
        self.current_balance += qty
        return self.current_balance

    def withdraw(self, qty):
        self.current_balance -= qty
        return self.current_balance

    def __init__(self, initial_money):
        self.current_balance = initial_money
        self.ops = {
            "deposit": self.deposit,
            "withdraw": self.withdraw
        }

    def process(self, op, qty):
        return self.ops[op](qty)