class BankAccount:
    def __init__(self, balance):
        self.balance = balance

    def process(self, action, amount = 0):
        if action == "get_balance":
            return self._get_balance()

        actions = {
            "deposit": self._deposit,
            "withdraw": self._withdraw,
            "transfer": self._transfer,
        }
        action = actions.get(action, None)
        if action is None:
            raise ValueError(f"Invalid action: {action}")
        
        return action(amount)
    
    def _deposit(self, amount):
        self.balance += amount
    
    def _withdraw(self, amount):
        self.balance -= amount
    
    def _get_balance(self):
        return self.balance
    
    def _transfer(self, amount):
        self.balance -= amount
        return amount

        
        