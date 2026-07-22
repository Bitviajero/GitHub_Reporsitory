@startuml
' Título
title Sistema de Gestión de Inventarios - UML

' Interfaz
interface IVendible {
    + double CalcularPrecioFinal()
}

' Clase abstracta
abstract class Producto {
    - string descripcion
    - double precio
    - int cantidad
    + string Descripcion { get; set; }
    + double Precio { get; set; }
    + int Cantidad { get; set; }
    + Producto(descripcion, precio, cantidad)
    + double CalcularTotal()
    + abstract void MostrarInformacion()
}

' Subclases (heredan de Producto)
class Teclado {
    - string tipo
    + Teclado(descripcion, precio, cantidad, tipo)
    + override void MostrarInformacion()
    + double CalcularPrecioFinal()   ' implementa IVendible
    + void MostrarTipo()
}

class Mouse {
    - string tipo
    + Mouse(descripcion, precio, cantidad, tipo)
    + override void MostrarInformacion()
    + double CalcularPrecioFinal()
    + void MostrarTipo()
}

class Monitor {
    - string resolucion
    + Monitor(descripcion, precio, cantidad, resolucion)
    + override void MostrarInformacion()
    + double CalcularPrecioFinal()
    + void MostrarResolucion()
}

class Impresora {
    - string tipoImpresion
    + Impresora(descripcion, precio, cantidad, tipoImpresion)
    + override void MostrarInformacion()
    + void MostrarTipoImpresion()
}

' Relaciones
Producto <|-- Teclado
Producto <|-- Mouse
Producto <|-- Monitor
Producto <|-- Impresora

IVendible <|.. Teclado   ' implementa
IVendible <|.. Mouse
IVendible <|.. Monitor

' Programa principal (opcional, para mostrar uso)
class Program {
    + Main(args)
}
note top of Program : Demuestra polimorfismo\nusando List<Producto>
@enduml