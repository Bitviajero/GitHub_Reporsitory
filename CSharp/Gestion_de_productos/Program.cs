using System;

// 1. Definición de la Clase (Molde para los objetos) [1]
public class Producto
{
    // 2. Atributos Privados (Encapsulamiento) [2, 3]
    private string descripcion;
    private double precio;
    private int cantidad;

    // 3. Constructor: Inicializa el objeto con valores válidos [4-6]
    public Producto(string descripcion, double precio, int cantidad)
    {
        this.descripcion = descripcion; // "this" referencia al atributo de la clase [7]
        this.precio = precio;
        this.cantidad = cantidad;
    }

    // 4. Propiedades (Métodos Get y Set para acceso controlado) [8-10]
    public string Descripcion
    {
        get { return descripcion; }
        set { descripcion = value; } // "value" es el parámetro implícito [11, 12]
    }

    public double Precio
    {
        get { return precio; }
        set { if (value >= 0) precio = value; } // Validación: evita precios negativos [13, 14]
    }

    public int Cantidad
    {
        get { return cantidad; }
        set { if (value >= 0) cantidad = value; }
    }

    // 5. Métodos de Comportamiento (Lógica de negocio) [15, 16]
    public double CalcularTotal()
    {
        return precio * cantidad;
    }

    public void MostrarInformacion()
    {
        Console.WriteLine($"Producto: {descripcion} | Precio: {precio:C} | Cantidad: {cantidad}");
        Console.WriteLine($"Total en Inventario: {CalcularTotal():C}");
    }
}

// Clase Principal: Punto de entrada de la aplicación [17, 18]
class Program
{
    static void Main(string[] args)
    {
        // 6. Instanciación: Creación del objeto Producto [19-21]
        Producto miProducto = new Producto("Teclado Mecánico", 45.50, 10);

        // Acceso a métodos mediante el operador punto (.) [19, 22]
        miProducto.MostrarInformacion();

        // Modificación de un atributo a través de su propiedad [23, 24]
        miProducto.Precio = 42.00;
        Console.WriteLine("\n--- Precio actualizado ---");
        miProducto.MostrarInformacion();
    }
}