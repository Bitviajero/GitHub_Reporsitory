// Programa 4: Interfaz IVendible
using System;

public interface IVendible
{
    double CalcularPrecioFinal();
}

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
    public abstract void MostrarInformacion();
}

public class Teclado : Producto, IVendible
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
    public double CalcularPrecioFinal()
    {
        return Precio * 1.21; // IVA
    }
}

public class Mouse : Producto, IVendible
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
    public double CalcularPrecioFinal()
    {
        return Precio * 1.21;
    }
}

// Impresora no implementa IVendible (a propósito)
public class Impresora : Producto
{
    private string tipoImpresion;
    public Impresora(string descripcion, double precio, int cantidad, string tipoImpresion)
        : base(descripcion, precio, cantidad)
    {
        this.tipoImpresion = tipoImpresion;
    }
    public override void MostrarInformacion()
    {
        Console.WriteLine($"Impresora: {Descripcion} | Precio: {Precio:C} | Cantidad: {Cantidad}");
        Console.WriteLine($"Total: {CalcularTotal():C}");
        Console.WriteLine($"Tipo de impresión: {tipoImpresion}");
    }
}

class Program
{
    static void Main()
    {
        Producto[] inventario = new Producto[]
        {
            new Teclado("Teclado Mecánico", 45.50, 10, "Mecánico"),
            new Mouse("Mouse Inalámbrico", 25, 15, "Inalámbrico"),
            new Impresora("Impresora Laser", 200, 3, "Laser")
        };

        foreach (Producto p in inventario)
        {
            p.MostrarInformacion();
            if (p is IVendible v)
                Console.WriteLine($"Precio final con IVA: {v.CalcularPrecioFinal():C}");
            Console.WriteLine();
        }
    }
}
