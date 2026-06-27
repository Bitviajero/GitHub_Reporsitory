class Persona:
    def __init__(self,nombre,edad):
        self.nombre = nombre
        self.edad = edad

    def saludar(self):
        print(f"Hola, minombre es {self.nombre} y tengo {self.edad} años.")

    def saludar_a(self, otra_persona):
        print(f"Hola {otra_persona.nombre}, soy {self.nombre} y tengo {self.edad} años. Encantado de conocerte.")
#Creacion e interaccion con el objeto
persona1= Persona("Alfonso",50)
persona1.saludar() #Imprime: Hola, mi nombre es Alfonso y tengo 50 años
persona2= Persona("Maria",30)
persona2.saludar() #Imprime: Hola, mi nombre es Maria y tengo 30 años
persona1.saludar_a(persona2) #Imprime: Hola Maria, soy Alfonso y tengo 50 años. Encantado de conocerte.