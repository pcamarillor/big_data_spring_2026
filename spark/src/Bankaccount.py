class BankAccount:
    def __init__(self,balance):
        self.balance = balance
        self.operations={
            'deposit':self.deposit,
            'withdraw':self.withdraw,
            'display':self.display
        }
    
    def deposit(self,amount):
        self.balance+=amount
    
    def withdraw(self,amount):
        self.balance-=amount
    
    
    def display(self):
        print(f'Balance: {self.balance}')
        
