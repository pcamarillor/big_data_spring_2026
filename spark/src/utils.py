class Student:
    def __init__(self, name, grade1):
        self._name = name
        self._grades = []
        self._grades.append(grade1)

    def __repr__(self):
        return f"Student(name={self._name})"


    def display(self):
        print(f"name:{self._name}")
        for g in self._grades:
            print(f"grade:{g}")

def squares(n):
    return n**2
        