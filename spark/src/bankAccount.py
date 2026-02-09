import random
import datetime
class BankAccount:
    def __init__ (self, initial_balance):
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self.creation_date = datetime.datetime.now()
        self.balance = initial_balance
    def deposit(self, amount):
        self.balance += amount
    def withdraw(self, amount):
        if amount > self.balance:
            raise Exception("Insufficient funds")
        self.balance -= amount
    def get_balance(self):
        return self.balance
    def account_info(self):
        cvv = random.randint(100, 999)
        return f"Current balance: {self.balance},\n cvv: {cvv}, \n expiration date: {self.creation_date + datetime.timedelta(days=365*5)}"
    def transfer( amount, account,target_account):
        account.withdraw(amount)
        target_account.deposit(amount)
        print(f"Transferred {amount} to target account. New balance: {account.get_balance()}")

    process = {
        "deposit": deposit,
        "withdraw": withdraw,
        "get_balance": get_balance,
        "account_info": account_info,
        "transfer": transfer
    }

if __name__ == "__main__":
    account = BankAccount(1000)
    print(account.account_info())
    account.deposit(500)
    print(account.get_balance())
    account2 = BankAccount(0)
    process["transfer"](200, account, account2)
    print(account.get_balance())
    print(account2.get_balance())
