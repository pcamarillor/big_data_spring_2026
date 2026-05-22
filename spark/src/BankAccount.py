class BankAccount:
    def __init__(self, initial_balance = 0.0):
        self._balance = initial_balance
        self._operations = {
            "deposit": self._deposit,
            "withdraw": self._withdraw,
            "get_balance": self._get_balance
        }

    def _deposit(self, amount: float):
        if amount <= 0: 
            return "Amount must be positive"
        self._balance += amount
        return self._balance

    def _withdraw(self, amount: float):
        if amount > self._balance: 
            return "Insufficient funds"
        self._balance -= amount
        return self._balance

    def _get_balance(self):
        return self._balance

    def process(self, operation_name: str, *args):
        if operation_name not in self._operations:
            return "Operation '{operation_name}' not supported."
        return self._operations[operation_name](*args)