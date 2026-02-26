class BankAccount:

    def __init__(self, balance):
        self.ops = {"deposit": self.deposit, "withdraw": self.withdraw, "get_balance":self.get_balance}
        self.balance = balance


    def deposit(self,amount):

        self.balance += amount

    def withdraw(self,amount):
        
        self.balance -= amount

    def get_balance(self,amount = None):
        
        print(f"The balance is: {self.balance}")

    def process(self, name, amount):

        if name == "deposit":
                self.deposit(amount)
        elif name == "withdraw":
                self.withdraw(amount)
        elif name == "get_balance":
                self.get_balance()