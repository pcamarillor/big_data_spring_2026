class BankAccount:
    def __init__(self, initial_balance):
        if initial_balance < 0:
            raise ValueError("El saldo inicial no puede ser negativo")
        self.balance = initial_balance
    
    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("El monto a depositar debe ser positivo")
        self.balance += amount
        return self.balance
    
    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("El monto a retirar debe ser positivo")
        if amount > self.balance:
            raise ValueError(f"Fondos insuficientes. Saldo actual: {self.balance}")
        self.balance -= amount
        return self.balance
    
    def process(self, operation, amount=None):
        operations = {
            'deposit': self.deposit,
            'withdraw': self.withdraw,
            'get_balance': self.get_balance,
        }
        
        if operation not in operations:
            raise ValueError(f"Operación '{operation}' no válida")
        
        if operation == 'get_balance':
            return operations[operation]()
        else:
            return operations[operation](amount)
    
    def get_balance(self):
        return self.balance
        
    def __str__(self):
        return f"El balance es de ${self.balance:.2f}"


