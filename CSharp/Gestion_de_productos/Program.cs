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

public class Teclado : Producto
{
    private string tipo;

    public Teclado(string descripcion, double precio, int cantidad, string tipo)
        : base(descripcion, precio, cantidad)
    {
        this.tipo = tipo;
    }

    public void MostrarTipo()
    {
        Console.WriteLine($"Tipo de Teclado: {tipo}");
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

    public void MostrarTipo()
    {
        Console.WriteLine($"Tipo de Mouse: {tipo}");
    }
}

public class Monitor : Producto
{
    private string resolucion;

    public Monitor(string descripcion, double precio, int cantidad, string resolucion)
        : base(descripcion, precio, cantidad)
    {
        this.resolucion = resolucion;
    }

    public void MostrarResolucion()
    {
        Console.WriteLine($"Resolución del Monitor: {resolucion}");
    }
}

public class Impresora : Producto
{
    private string tipoImpresion;

    public Impresora(string descripcion, double precio, int cantidad, string tipoImpresion)
        : base(descripcion, precio, cantidad)
    {
        this.tipoImpresion = tipoImpresion;
    }

    public void MostrarTipoImpresion()
    {
        Console.WriteLine($"Tipo de Impresora: {tipoImpresion}");
    }
}


// Clase Principal: Punto de entrada de la aplicación [17, 18]
class Program
{
    static void Main(string[] args)
    {
        // 6. Instanciación: Creación del objeto Producto [19-21]
        Teclado miTeclado = new Teclado("Teclado Mecánico", 45.50, 10, "Mecánico");
        Mouse miMouse = new Mouse("Mouse Inalámbrico", 25.00, 15, "Inalámbrico");
        Monitor miMonitor = new Monitor("Monitor 24 pulgadas", 150.00, 5, "1920x1080");
        Impresora miImpresora = new Impresora("Impresora Laser", 200.00, 3, "Laser");

        // Acceso a métodos mediante el operador punto (.) [19, 22]
        miTeclado.MostrarInformacion();
        miTeclado.MostrarTipo();
        miMouse.MostrarInformacion();
        miMouse.MostrarTipo();
        miMonitor.MostrarInformacion();
        miMonitor.MostrarResolucion();
        miImpresora.MostrarInformacion();
        miImpresora.MostrarTipoImpresion();

        // Modificación de un atributo a través de su propiedad [23, 24]
        miTeclado.Precio = 42.00;
        miMonitor.Precio = 140.00;
        miImpresora.Precio = 180.00;
        Console.WriteLine("\n--- Precio actualizado ---");
        miTeclado.MostrarInformacion();
        miMonitor.MostrarInformacion();
        miImpresora.MostrarInformacion();
    }
}