class BankAccount:
    def __init__(self, initial_balance=0):
        super().__init__()

        if initial_balance < 0:
            print("WARNING: Initial balance cannot be negative. New balance = 0.")
            initial_balance = 0
        self.balance = initial_balance
        self.operations = {
            "deposit": self.deposit,
            "withdraw": self.withdraw,
            "get_balance": self.get_balance
        }

    def deposit(self, amount):
        if amount < 0:
            print("WARNING: Deposit amount cannot be negative")
            return False
        
        self.balance += amount
        print(f"{amount} deposited. New balance: {self.balance}")
        return True

    def withdraw(self, amount):
        if amount <= 0:
            print("WARNING: Withdrawal amount cannot be negative or null")
            return False
        if amount > self.balance:
            print("WARNING: Insufficient funds")
            return False
        
        self.balance -= amount
        print(f"{amount} withdrawn. New balance: {self.balance}")
        return True
    
    def get_balance(self):
        print(f"Current balance: {self.balance}")
        return self.balance

    def process(self, operation, amount=0):
        if operation not in self.operations:
            print("WARNING: Invalid operation")
            return False
        
        operation_func = self.operations[operation]

        if amount != 0:
            return operation_func(amount)
        else:
            return operation_func()
