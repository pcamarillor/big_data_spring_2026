class BankAccount:
    def __init__(self, initial_balance=0):
        self.__balance = initial_balance
    
        self.operations = {
            "deposit": self.__deposit,
            "withdraw": self.__withdraw,
            "get_balance": self.__get_balance
        }

    def __deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            return f"Deposited: {amount}. New balance: {self.__balance}"
        return "Invalid deposit amount."

    def __withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            return f"Withdrew: {amount}. New balance: {self.__balance}"
        return "Insufficient funds or invalid amount."

    def __get_balance(self, *args):
        return f"Current balance: {self.__balance}"

    def process(self, operation_name, amount=None):
        operation = self.operations.get(operation_name)
        
        if operation:
            # Ejecución dinámica basada en si la operación requiere argumentos
            if operation_name == "get_balance":
                return operation()
            return operation(amount) if amount is not None else "Amount required for this operation."
        else:
            return f"Operation '{operation_name}' not found."