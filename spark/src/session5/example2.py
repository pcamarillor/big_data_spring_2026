class Person2:
    def __init__(self, name):
        self._name=name

    def say_hello(self):
        print(f"hi {self._name}")

if __name__ == "__main__":
    p = Person2("test")
    p.say_hello()