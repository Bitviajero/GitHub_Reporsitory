class Persona:
    def __init__(self,nombre,edad):
        self.nombre = nombre
        self.edad = edad

    def saludar(self):
        print(f"Hola, minombre es {self.nombre} y tengo {self.edad} años.")
#Creacion e interaccion con el objeto
persona1= Persona("Alfonso Rios",50)
persona1.saludar() #Imprime: Hola, mi nombre es Alfonso y tengo 50 años