import math
class Figura:
    def calcular_area(self):
        pass # Este método será implementado en las subclases
class Cuadrado(Figura):
    def __init__(self, lado):
        self.lado=lado
    def calcular_area(self):
        return self.lado * self.lado
class Circulo(Figura):
    def __init__(self,radio):
        self.radio=radio
    def calcular_area(self):
        return math.pi * (self.radio**2)
#Crear instancias y calcular el área
cuadrado=Cuadrado(4)
circulo=Circulo(3)
print(cuadrado.calcular_area()) #Salida: 16
print(circulo.calcular_area()) #Salida: 28.27
    