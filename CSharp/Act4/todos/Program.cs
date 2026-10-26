using System;
using System.Collections.Generic;

// ====================================================
// 1. INTERFAZ: contrato para productos vendibles
// ====================================================
public interface IVendible
{
    double CalcularPrecioFinal(); // Aplica IVA o descuento
}

// ====================================================
// 2. CLASE ABSTRACTA Producto (base para todos)
// ====================================================
public abstract class Producto
{
    // Atributos privados (encapsulamiento)
    private string descripcion;
    private double precio;
    private int cantidad;

    // Constructor
    public Producto(string descripcion, double precio, int cantidad)
    {
        this.descripcion = descripcion;
        this.precio = precio;
        this.cantidad = cantidad;
    }

    // Propiedades
    public string Descripcion
    {
        get { return descripcion; }
        set { descripcion = value; }
    }

    public double Precio
    {
        get { return precio; }
        set { if (value >= 0) precio = value; }
    }

    public int Cantidad
    {
        get { return cantidad; }
        set { if (value >= 0) cantidad = value; }
    }

    // Método concreto (compartido por todas las subclases)
    public double CalcularTotal()
    {
        return precio * cantidad;
    }

    // MÉTODO ABSTRACTO: obliga a cada subclase a implementar su propia versión
    public abstract void MostrarInformacion();
																								  
																	   
	 
}

// ====================================================
// 3. SUBCLASES (heredan de Producto e implementan IVendible)
// ====================================================

public class Teclado : Producto, IVendible
{
    private string tipo;

    public Teclado(string descripcion, double precio, int cantidad, string tipo)
        : base(descripcion, precio, cantidad)
    {
        this.tipo = tipo;
    }

    // Implementación del método abstracto
    public override void MostrarInformacion()
    {
        Console.WriteLine($"Teclado: {Descripcion} | Precio: {Precio:C} | Cantidad: {Cantidad} | Tipo: {tipo}");
        Console.WriteLine($"Total en inventario: {CalcularTotal():C}");
    }

    // Implementación de la interfaz IVendible
    public double CalcularPrecioFinal()
    {
        // Aplica 16% de IVA
        return Precio * 1.16;
    }

    // Método específico de Teclado
    public void MostrarTipo()
    {
        Console.WriteLine($"Tipo de Teclado: {tipo}");
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
        Console.WriteLine($"Mouse: {Descripcion} | Precio: {Precio:C} | Cantidad: {Cantidad} | Tipo: {tipo}");
        Console.WriteLine($"Total en inventario: {CalcularTotal():C}");
    }

    public double CalcularPrecioFinal()
    {
        return Precio * 1.16; // IVA
    }

    public void MostrarTipo()
    {
        Console.WriteLine($"Tipo de Mouse: {tipo}");
    }
}

public class Monitor : Producto, IVendible
{
    private string resolucion;

    public Monitor(string descripcion, double precio, int cantidad, string resolucion)
        : base(descripcion, precio, cantidad)
    {
        this.resolucion = resolucion;
    }

    public override void MostrarInformacion()
    {
        Console.WriteLine($"Monitor: {Descripcion} | Precio: {Precio:C} | Cantidad: {Cantidad} | Resolución: {resolucion}");
        Console.WriteLine($"Total en inventario: {CalcularTotal():C}");
    }

    public double CalcularPrecioFinal()
    {
        return Precio * 1.16;
    }

    public void MostrarResolucion()
    {
        Console.WriteLine($"Resolución del Monitor: {resolucion}");
    }
}

// Impresora NO implementa IVendible (para mostrar que no todas las clases deben hacerlo)
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
        Console.WriteLine($"Impresora: {Descripcion} | Precio: {Precio:C} | Cantidad: {Cantidad} | Tipo impresión: {tipoImpresion}");
        Console.WriteLine($"Total en inventario: {CalcularTotal():C}");
    }

    public void MostrarTipoImpresion()
    {
        Console.WriteLine($"Tipo de Impresora: {tipoImpresion}");
    }
}

// ====================================================
// 4. PROGRAMA PRINCIPAL (demostración de polimorfismo)
// ====================================================
class Program
{
    static void Main(string[] args)
    {
        // Creamos una lista de Producto (polimorfismo)
        List<Producto> inventario = new List<Producto>
        {
            new Teclado("Teclado Mecánico", 45.50, 10, "Mecánico"),
            new Mouse("Mouse Inalámbrico", 25.00, 15, "Inalámbrico"),
            new Monitor("Monitor 24 pulgadas", 150.00, 5, "1920x1080"),
            new Impresora("Impresora Laser", 200.00, 3, "Laser")
        };

        Console.WriteLine("=== INVENTARIO COMPLETO (polimorfismo) ===\n");
        foreach (Producto prod in inventario)
        {
            prod.MostrarInformacion(); // Llamada polimórfica
								
									 
							  
									   
									  
										 
										   

            // Verificamos si el producto implementa IVendible
            if (prod is IVendible vendible)
            {
                Console.WriteLine($"Precio final con IVA: {vendible.CalcularPrecioFinal():C}");
            }
            Console.WriteLine(); // línea en blanco
        }

        // Demostración adicional: modificar precios mediante propiedades
        Console.WriteLine("=== ACTUALIZACIÓN DE PRECIOS ===\n");
        inventario[0].Precio = 42.00;
        inventario[2].Precio = 140.00;
        inventario[3].Precio = 180.00;

        foreach (Producto prod in inventario)
        {
            prod.MostrarInformacion();
            Console.WriteLine();
        }
    }
}