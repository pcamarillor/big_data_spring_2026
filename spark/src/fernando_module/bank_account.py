class BankAccount:
    def __init__(self, saldo_inicial=0):
        self.saldo = saldo_inicial
        # Este diccionario sirve para relacionar el nombre de la acción con la función que la realiza
        self.acciones = {
            "deposit": self.deposit,
            "withdraw": self.withdraw,
            "get_balance": self.get_balance
        }

    def deposit(self, cantidad):
        if cantidad <= 0:
            print("No se puede depositar una cantidad menor o igual a cero.")
            return
        # Sumamos la cantidad al saldo
        self.saldo += cantidad
        print(f"Depósito realizado: {cantidad}. Saldo actual: {self.saldo}")

    def withdraw(self, cantidad):
        if cantidad > self.saldo:
            print(f"Fondos insuficientes. Saldo disponible: {self.saldo}")
            return
        # Restamos la cantidad al saldo
        self.saldo -= cantidad
        print(f"Retiro realizado: {cantidad}. Saldo actual: {self.saldo}")

    def get_balance(self, _=None):
        print(f"Saldo actual: {self.saldo}")
        return self.saldo

    def process(self, nombre_accion, cantidad=None):
        #Ejecuta una acción según el nombre recibido para ver qué hacer sin usar muchos if.
        if nombre_accion in self.acciones:
            accion = self.acciones[nombre_accion]
            # Por si la acción necesita una cantidad
            accion(cantidad)

