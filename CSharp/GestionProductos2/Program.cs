using System;  // Importa el espacio de nombres que contiene Console, entre otros.

// ==================================================
// 1. DEFINICIÓN DE LA CLASE Producto
// ==================================================
// Una clase es un "molde" o "plantilla" para crear objetos.
// Los objetos son instancias de una clase, con datos (atributos) y comportamientos (métodos).
// ==================================================
public class Producto
{
    // ==============================================
    // 2. ATRIBUTOS (CAMPOS) PRIVADOS
    // ==============================================
    // Son las características internas del objeto.
    // Se declaran con "private" para que solo la clase pueda acceder a ellos directamente.
    // Esto es parte del ENCAPSULAMIENTO (ocultar detalles internos).
    // ==============================================

    private string descripcion;   // Almacena el nombre o descripción del producto.
    private double precio;        // Almacena el precio unitario (con decimales).
    private int cantidad;         // Almacena la cantidad disponible en inventario.

    // ==============================================
    // 3. CONSTRUCTOR
    // ==============================================
    // El constructor se llama automáticamente cuando se crea un objeto con "new".
    // Su propósito es inicializar los atributos del objeto con valores válidos.
    // Tiene el mismo nombre que la clase y no devuelve ningún tipo (ni siquiera void).
    // ==============================================

    public Producto(string descripcion, double precio, int cantidad)
    {
        // La palabra clave "this" se refiere al objeto actual (la instancia).
        // Se usa para distinguir entre el parámetro y el atributo de la clase.
        this.descripcion = descripcion; // Asigna el parámetro al atributo privado.
        this.precio = precio;
        this.cantidad = cantidad;
    }

    // ==============================================
    // 4. PROPIEDADES (GET y SET)
    // ==============================================
    // Las propiedades permiten un acceso controlado a los atributos privados.
    // Ofrecen una forma segura de leer (get) y modificar (set) los datos.
    // Pueden incluir lógica adicional, como validaciones.
    // ==============================================

    // Propiedad para "descripcion"
    public string Descripcion
    {
        get { return descripcion; }     // Devuelve el valor del atributo privado.
        set { descripcion = value; }    // Asigna un nuevo valor. "value" es la palabra clave que representa el valor que se está asignando.
    }

    // Propiedad para "precio" con validación
    public double Precio
    {
        get { return precio; }
        set
        {
            // Aquí se valida que el precio no sea negativo.
            // Si es menor que 0, no se asigna (se mantiene el valor anterior).
            if (value >= 0)
                precio = value;
            // Si no se cumple, simplemente no se hace nada (podríamos lanzar una excepción).
        }
    }

    // Propiedad para "cantidad" con validación
    public int Cantidad
    {
        get { return cantidad; }
        set
        {
            if (value >= 0)
                cantidad = value;
        }
    }

    // ==============================================
    // 5. MÉTODOS (COMPORTAMIENTO)
    // ==============================================
    // Los métodos definen las acciones que puede realizar el objeto.
    // Pueden usar los atributos internos y devolver resultados.
    // ==============================================

    // Método que calcula el valor total del inventario para este producto.
    // Devuelve un double (el resultado de multiplicar precio por cantidad).
    public double CalcularTotal()
    {
        return precio * cantidad;
    }

    // Método que muestra la información del producto en la consola.
    // No devuelve nada (void), solo imprime en la pantalla.
    public void MostrarInformacion()
    {
        // Console.WriteLine escribe una línea de texto en la consola.
        // La $ antes de la cadena permite interpolación: insertar variables dentro de {}
        // :C da formato de moneda (depende de la configuración regional del sistema).
        Console.WriteLine($"Producto: {descripcion} | Precio: {precio:C} | Cantidad: {cantidad}");
        Console.WriteLine($"Total en Inventario: {CalcularTotal():C}");
    }
}

// ==================================================
// 6. CLASE PRINCIPAL (Program)
// ==================================================
// Todo programa en C# necesita un punto de entrada: el método Main.
// Es el primer código que se ejecuta al iniciar la aplicación.
// ==================================================

class Program
{
    // El método Main es estático (pertenece a la clase, no a un objeto).
    // Su firma es: static void Main(string[] args)
    // "args" contiene los argumentos de la línea de comandos (opcional).
    static void Main(string[] args)
    {
        // ==============================================
        // 7. INSTANCIACIÓN Y USO DE OBJETOS
        // ==============================================
        // Creamos un objeto de tipo Producto usando la palabra clave "new".
        // Llamamos al constructor y le pasamos los valores iniciales.
        // ==============================================

        Producto miProducto = new Producto("Teclado Mecánico", 45.50, 10);

        // ==============================================
        // 8. LLAMADA A MÉTODOS
        // ==============================================
        // Usamos el operador punto (.) para acceder a los miembros públicos del objeto.
        // ==============================================

        miProducto.MostrarInformacion();

        // ==============================================
        // 9. MODIFICACIÓN DE ATRIBUTOS A TRAVÉS DE PROPIEDADES
        // ==============================================
        // Asignamos un nuevo precio usando la propiedad Precio.
        // La validación dentro de la propiedad verificará que el valor sea >= 0.
        // ==============================================

        miProducto.Precio = 42.00;  // Cambiamos el precio a 42.00

        Console.WriteLine("\n--- Precio actualizado ---");
        miProducto.MostrarInformacion();

        // ==============================================
        // 10. ESPERA PARA VER LA SALIDA
        // ==============================================
        // Si ejecutas en consola, la ventana se cerrará rápido.
        // ReadKey() pausa la ejecución hasta que presiones una tecla.
        // ==============================================

        Console.WriteLine("\nPresiona cualquier tecla para salir...");
        Console.ReadKey();
    }
}
