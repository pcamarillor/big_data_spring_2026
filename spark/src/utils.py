class Student:
    def __init__(self, name, grade1):
        self._name = name
        self._grades = []
        self._grades.append(grade1)

    def __repr__(self):
        return f"Student(name={self._name})"

    def display(self):
        print(f"name: {self._name}")
        for g in self._grades:
            print(f"grade: {g}")



class BankAccount:
    def __init__(self, saldo_inicial: float):
        self.saldo = saldo_inicial
        
        self.operaciones = {
            "depositar": self.depositar,
            "retirar": self.retirar,
            "consultar_saldo": self.consultar_saldo
        }

    def depositar(self, monto: float):
        if monto <= 0:
            return "El monto debe ser positivo"
        self.saldo += monto
        return f"Se depositaron {monto}. Saldo actual: {self.saldo}"

    def retirar(self, monto: float):
        if monto <= 0:
            return "El monto debe ser positivo"
        if monto > self.saldo:
            return "Fondos insuficientes"
        self.saldo -= monto
        return f"Se retiraron {monto}. Saldo actual: {self.saldo}"

    def consultar_saldo(self):
        return f"Saldo actual: {self.saldo}"

    def process(self, nombre_operacion: str, *args):
        if nombre_operacion not in self.operaciones:
            return f"Operación '{nombre_operacion}' no válida"

        return self.operaciones[nombre_operacion](*args)
