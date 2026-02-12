class student:
    def __init__(self,name,grade_1):
        self.name=name
        self.grades= []
        self.grade_1=grade_1
    
    def display(self):
        print(f"Student: {self.name}")
        print(f"Grade 1: {self.grade_1}")
        
    def __repr__(self):
        pass
    
    def squares(n):
        return n**2
    