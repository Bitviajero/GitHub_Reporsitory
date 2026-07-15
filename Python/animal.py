class Animal:
    def hacer_sonido(self):
        print("Sonido genérico de animal")

class Perro(Animal):
    def hacer_sonido(self):
        print("Guau")
# Crear una instancia de Perro y llamar al método
mi_perro = Perro()
mi_perro.hacer_sonido() # Salida: Guau