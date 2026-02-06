class BankAccount:
    def __init__(self, int_balance=0):
        self._current_balance = int_balance

        self._operations = {
            "deposit": self.deposit,
            "withdraw": self.withdraw,
            "balance": self.balance
        }
    
    def deposit(self, amount):
        if amount > 0:
            self._current_balance += amount
            print(f"Deposited {amount}")
        else:
            print("Can't deposit")

    def withdraw(self, amount):
        if amount > 0 and amount <= self._current_balance:
            self._current_balance -= amount
            print(f"Withdrew {amount}")
        else:
            print("Can't withdraw")
    
    def balance(self):
        print(f"Balance: {self._current_balance}")

