class BankAccount:
    def __init__(self, initial_balance=0):
        self._balance = initial_balance

        self._operations = {
            "deposit": self._deposit,
            "withdraw": self._withdraw,
            "get_balance": self._get_balance
        }

    def _deposit(self, amount):
        self._balance += amount
        return self._balance

    def _withdraw(self, amount):
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        return self._balance

    def _get_balance(self):
        return self._balance

    def process(self, operation, *args):
        if operation not in self._operations:
            raise ValueError(f"Operation '{operation}' not supported")

        return self._operations[operation](*args)
