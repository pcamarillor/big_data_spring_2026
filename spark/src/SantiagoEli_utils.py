class Student:
    def __init__(self, name, grade_1):
        self._name = name
        self._grades = []
        self._grades.append(grade_1)

    def display(self):
        print(f"Name: {self._name}, Grades: {self._grades}")
        for g in self._grades:
            print(f"Grade: {g}")

    def __repr__(self):
        return f"Student(Name: {self._name})"
    



class BankAccount:
    def __init__(self, balance):
        self._balance = balance

        # Store functions in a dictionary
        self.process = {
        'deposit': self.deposit,
        'withdraw': self.withdraw,
        'get_balance': self.get_balance
        }

    def deposit(self, amount):
        self._balance += amount

    def withdraw(self, amount): 
        if amount <= self._balance:
            self._balance -= amount
        else:
            print("Insufficient funds")
    
    def get_balance(self):
        return self._balance

    def display(self):
        print(f"Balance: {self._balance}")

    def __repr__(self):
        return f"BankAccount(Balance: {self._balance})"