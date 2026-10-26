class Animal:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self.edad = edad

    def comer(self):
        print(f"{self.nombre} está comiendo.")

    def dormir(self):
        print(f"{self.nombre} está durmiendo.")

class Perro(Animal):   # en esta linea se define la clase Perro que hereda de la clase Animal
    def __init__(self, nombre, edad, raza): # en esta linea se agrega el atributo raza a la clase Perro, que hereda de la clase Animal los atributos nombre y edad
        super().__init__(nombre, edad) # en esta linea se llama al constructor de la clase padre (Animal) para inicializar los atributos nombre y edad
        self.raza = raza   # en esta linea se inicializa el atributo raza de la clase Perro

    def ladrar(self):   # en esta linea se define el metodo ladrar de la clase Perro
        print(f"{self.nombre} está ladrando.")   # en esta linea se imprime el mensaje de que el perro está ladrando, usando el atributo nombre de la clase padre (Animal)
#hasta aqui el codigo no imprime nada, solo define las clases y sus metodos
animal = Animal("Firulais", 5)  # en esta linea se crea un objeto de la clase Animal llamado animal, con los atributos nombre y edad
animal.comer() # en esta linea se llama al metodo comer del objeto animal, que imprime el mensaje de que el animal está comiendo
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

class vaca(Animal):
    def __init__(self, nombre, edad, peso):
        super().__init__(nombre, edad)
        self.peso = peso
    
    def mugir(self):
        print(f"{self.nombre} esta mugiendo, tiene {self.peso} kg de peso.")

vaca = vaca("la vaca", 4, 500)
vaca.comer()
vaca.dormir()
vaca.mugir()