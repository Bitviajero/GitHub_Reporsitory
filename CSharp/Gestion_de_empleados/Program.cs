using System;

// 1. Declaración de la Clase: Es la plantilla o modelo (Unidad 2, pág. 1) [1, 2]
public class Empleado
{
    // 2. Atributos: Datos protegidos mediante encapsulamiento (Unidad 2, pág. 3, 10) [3, 4]
    private string nombre;
    private double salario;

    // 3. Constructor: Inicializa los atributos al crear el objeto (Unidad 2, pág. 7, 8) [5, 6]
    public Empleado(string nombre, double salario)
    {
        // Se usa 'this' para referirse al atributo del objeto actual (Unidad 2, pág. 6) [7]
        this.nombre = nombre;
        this.salario = salario;
    }

    // 4. Métodos: Definen las acciones que el objeto puede realizar (Unidad 2, pág. 1, 13) [1, 4]
    public void MostrarInformacion()
    {
        Console.WriteLine($"Empleado: {nombre} | Salario: {salario:C}");
    }

    public void AplicarBono(double bono)
    {
        salario += bono;
        Console.WriteLine($"Bono de {bono:C} aplicado a {nombre}.");
    }
}

// Programa Principal (Controlador)
class Program
{
    static void Main()
    {
        // 5. Instanciación: Creación de un ejemplar específico de la clase (Unidad 2, pág. 5, 6) [7, 8]
        Empleado miEmpleado = new Empleado("Carlos Pérez", 1500.00);

        // Prueba de los métodos
        Console.WriteLine("--- Estado Inicial ---");
        miEmpleado.MostrarInformacion();

        Console.WriteLine("\n--- Procesando Pago ---");
        miEmpleado.AplicarBono(200.00);
        miEmpleado.MostrarInformacion();
    }
}
