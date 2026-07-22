// Programa 2: Herencia simple (Producto como base concreta)
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

public class Teclado : Producto
{
    private string tipo;
    public Teclado(string descripcion, double precio, int cantidad, string tipo)
        : base(descripcion, precio, cantidad)
    {
        this.tipo = tipo;
    }
    public void MostrarTipo() => Console.WriteLine($"Tipo: {tipo}");
}

public class Mouse : Producto
{
    private string tipo;
    public Mouse(string descripcion, double precio, int cantidad, string tipo)
        : base(descripcion, precio, cantidad)
    {
        this.tipo = tipo;
    }
    public void MostrarTipo() => Console.WriteLine($"Tipo: {tipo}");
}

class Program
{
    static void Main()
    {
        Teclado t = new Teclado("Teclado Mecánico", 45.50, 10, "Mecánico");
        Mouse m = new Mouse("Mouse Inalámbrico", 25, 15, "Inalámbrico");
        t.MostrarInformacion();
        t.MostrarTipo();
        m.MostrarInformacion();
        m.MostrarTipo();
    }
}