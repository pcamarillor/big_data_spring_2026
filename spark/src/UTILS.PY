class Estudiante:
    def __init__(self, nombre, nota1):
        self._nombre = nombre
        self._notas = []
        self._notas.append(nota1)

    def __repr__(self):
        return f"Estudiante(nombre='{self._nombre}')"

    def mostrar_datos(self):
        print(f"Nombre: {self._nombre}")
        for nota in self._notas:
            print(f"Nota: {nota}")

