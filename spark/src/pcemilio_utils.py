class student:
    def __init__(self,name,grade_1):
        self._name = name
        self._grades = []
        self._grades_append(grade_1)
        
    def display(self):
        print(f"name{self._name}")
        print("grades")
        for g in self._grades:
            print(g)
    
    def _repr_(self):
        print("Student(name:{self._name})")
              