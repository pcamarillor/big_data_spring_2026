class BankAccount:
    # constructor
    def __init__(self, balance: float):
        if balance < 0:
            raise ValueError("Initial balance cannot be negative")
        # end if

        self._balance = balance
        self._operations = {
            "deposit": self.deposit,
            "withdraw": self.withdraw,
            "get_balance": self.get_balance
        }
    # end def

    def __str__(self):
        return f"Balance: {self._balance}"
    # end def

    def __repr__(self):
        return f"BankAccount(balance={self._balance})"
    # end def

    # getters
    @property
    def balance(self):
        return self._balance
    # end def

    def get_balance(self):
        return self._balance
    # end def

    # methods
    def process(self, operation: str, amount: float = None):
        if operation not in self._operations:
            raise ValueError(f"Invalid operation: {operation}")
        # end if

        if operation == "get_balance":
            return self._operations[operation]()
        else:
            self._operations[operation](amount)
        # end if-else
    # end def

    def deposit(self, amount: float):
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative")
        # end if
        
        self._balance += amount
    # end def

    def withdraw(self, amount: float):
        if amount < 0:
            raise ValueError("Withdraw amount cannot be negative")
        # end if

        if amount > self._balance:
            raise ValueError("Insufficient funds")
        # end if

        self._balance -= amount
    # end def
# end class