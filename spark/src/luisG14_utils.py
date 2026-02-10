class Student: 
    def __init__(self, name, grade_1):
        self._name = name
        self._grades = []
        self._grades.append(grade_1)
        
    def display(self):
        print(f"name:{self._name}")
        print(f"grades")
        for g in self._grades:
            print(g)

    def __repr__(self):
        return (f"Student(name :{self._name})")
        