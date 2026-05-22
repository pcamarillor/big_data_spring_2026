class BankAccount:
    def __init__(self, initial_balance=0.0):
        """Inicializa la cuenta bancaria con un saldo inicial y un diccionario de operaciones."""

        self._balance = initial_balance

        self._operations = {
            "deposit": self._deposit,
            "withdraw": self._withdraw,
            "get_balance": self._get_balance
        }

    def _deposit(self, amount):
        if amount <= 0:
            raise ValueError("La cantidad a depositar debe ser positiva.")
        
        self._balance += amount
        return f"Depósito: ${amount}. Nuevo Saldo: ${self._balance}"

    def _withdraw(self, amount):
        if amount <= 0:
            raise ValueError("La cantidad a retirar debe ser positiva.")
        
        if amount > self._balance:
            raise ValueError(f"Fondos insuficientes. Saldo actual: ${self._balance}")
        
        self._balance -= amount
        return f"Retiro: ${amount}. Nuevo Saldo: ${self._balance}"

    def _get_balance(self):
        return f"Saldo actual: ${self._balance}"

    def process(self, operation_name, *args):
        action = self._operations.get(operation_name)

        if not action:
            return f"Error: La operación '{operation_name}' no es válida."
        
        try:
            return action(*args)
        except TypeError:
            return f"Error: Número de argumentos incorrecto para '{operation_name}'."
        except ValueError as e:
            return f"Error: {e}"