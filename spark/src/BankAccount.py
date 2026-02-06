class BanckAccount:
    
    def __init__(self,amount):
        self.amount=amount

    def __repr__(self):
        return f"amount={self.amount}"    
    
    def deposit(self,value):
        self.amount+=value

    def withdraw(self,value):
        self.amount-=value

    def get_balance(self):
        print(f"Actual amount={self.amount}") 

    def process(self, opcion,value=None):

        opciones={
        'deposit':self.deposit,
        'withdraw':self.withdraw,
        'get_balance':self.get_balance
        }    
        
        if value is not None:
            opciones[opcion](value)
        else:
            opciones[opcion]()


        '''if opcion in opciones:
            if value is not None:
                return opciones[opcion](value)
            else:
                return opciones[opcion]()    
        else:
            return 'opcion no valida'
       '''
        


