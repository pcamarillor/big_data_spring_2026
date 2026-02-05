class Student:
    def __init__(self, name, degree):
        self.name = name
        self.degree = degree
    
    def information(self):
        print(f"HOLA CHAMBAMASTERS, LLEGO A USTEDES {self.name} DESDE {self.degree}")