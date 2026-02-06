class BanckAccunt():
    def __init__(self, open):
        self.cuenta = open

    def process(self, move, cant=None):
        if move == "deposit":
            self.cuenta += cant

        elif move == "withdraw":
            if cant > self.cuenta:
                print(f"Erro: No hay suficiente dinero en la cuenta. No puedes retirar ${cant} dólares")
            else:
                self.cuenta -= cant

        elif move == "get_balance":
            print(f"El balance es de {self.cuenta}")
