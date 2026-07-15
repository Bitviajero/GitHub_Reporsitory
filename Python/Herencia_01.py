class Animal:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self.edad = edad

    def comer(self):
        print(f"{self.nombre} está comiendo.")

    def dormir(self):
        print(f"{self.nombre} está durmiendo.")

class Perro(Animal):
    def __init__(self, nombre, edad, raza):
        super().__init__(nombre, edad)
        self.raza = raza

    def ladrar(self):
        print(f"{self.nombre} está ladrando.")
#hasta aqui el codigo no imprime nada, solo define las clases y sus metodos
animal = Animal("Firulais", 5)
animal.comer()
animal.dormir()

perro = Perro("Firulais", 5, "Golden Retriever")
perro.comer()
perro.dormir()
perro.ladrar()

perro = Perro("Firulais", 5, "Golden Retriever")
print(f"{perro.nombre} tiene {perro.edad} años y es de raza {perro.raza}.")


class gato(Animal):
    def __init__(self, nombre, edad, color):
        super().__init__(nombre, edad)
        self.color = color

    def maullar(self):
        print(f"{self.nombre} está maullando.")

gato = gato("Michi", 3, "Blanco")
gato.comer()
gato.dormir()
gato.maullar()