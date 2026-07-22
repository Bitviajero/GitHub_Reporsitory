// Programa 1: Clase Producto concreta, sin herencia ni polimorfismo
using System;

public class Producto
{
    private string descripcion;
    private double precio;
    private int cantidad;

    public Producto(string descripcion, double precio, int cantidad)
    {
        this.descripcion = descripcion;
        this.precio = precio;
        this.cantidad = cantidad;
    }

    public string Descripcion { get => descripcion; set => descripcion = value; }
    public double Precio { get => precio; set => precio = value; }
    public int Cantidad { get => cantidad; set => cantidad = value; }

    public double CalcularTotal() => precio * cantidad;
    public void MostrarInformacion()
    {
        Console.WriteLine($"Producto: {descripcion} | Precio: {precio:C} | Cantidad: {cantidad}");
        Console.WriteLine($"Total: {CalcularTotal():C}");
    }
}

class Program
{
    static void Main()
    {
        Producto p = new Producto("Laptop", 800, 5);
        p.MostrarInformacion();
    }
}