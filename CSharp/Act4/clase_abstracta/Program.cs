// Programa 3: Clase abstracta y método abstracto
using System;

public abstract class Producto
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
    public abstract void MostrarInformacion(); // Ahora abstracto
}

public class Teclado : Producto
{
    private string tipo;
    public Teclado(string descripcion, double precio, int cantidad, string tipo)
        : base(descripcion, precio, cantidad)
    {
        this.tipo = tipo;
    }
    public override void MostrarInformacion()
    {
        Console.WriteLine($"Teclado: {Descripcion} | Precio: {Precio:C} | Cantidad: {Cantidad}");
        Console.WriteLine($"Total: {CalcularTotal():C}");
        Console.WriteLine($"Tipo: {tipo}");
    }
}

public class Mouse : Producto
{
    private string tipo;
    public Mouse(string descripcion, double precio, int cantidad, string tipo)
        : base(descripcion, precio, cantidad)
    {
        this.tipo = tipo;
    }
    public override void MostrarInformacion()
    {
        Console.WriteLine($"Mouse: {Descripcion} | Precio: {Precio:C} | Cantidad: {Cantidad}");
        Console.WriteLine($"Total: {CalcularTotal():C}");
        Console.WriteLine($"Tipo: {tipo}");
    }
}

class Program
{
    static void Main()
    {
        Producto p1 = new Teclado("Teclado Mecánico", 45.50, 10, "Mecánico");
        Producto p2 = new Mouse("Mouse Inalámbrico", 25, 15, "Inalámbrico");
        p1.MostrarInformacion();
        Console.WriteLine();
        p2.MostrarInformacion();
    }
}