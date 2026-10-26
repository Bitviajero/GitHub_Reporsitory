using System;
using System.Collections.Generic;

// ====================================================
// DEFINICIÓN DE CLASES (FUERA DEL Main)
// ====================================================
public abstract class Producto
{
    // Atributos, propiedades, métodos...
    public double CalcularTotal()
    {
        return precio * cantidad;   // Esta operación está dentro del objeto
    }
    public abstract void MostrarInformacion();
}

public class Teclado : Producto, IVendible
{
    // ...
}

// ====================================================
// PROGRAMA PRINCIPAL (PUNTO DE ENTRADA)
// ====================================================
class Program
{
    static void Main(string[] args)
    {
        // Aquí dentro van las OPERACIONES:

        // 1. Crear objetos
        Teclado miTeclado = new Teclado("Teclado Mecánico", 45.50, 10, "Mecánico");
        Mouse miMouse = new Mouse("Mouse Inalámbrico", 25.00, 15, "Inalámbrico");

        // 2. Llamar a métodos de los objetos
        miTeclado.MostrarInformacion();   // Esto ejecuta el método definido en Teclado

        // 3. Hacer cálculos adicionales (fuera de los objetos)
        double totalInventario = miTeclado.CalcularTotal() + miMouse.CalcularTotal();
        Console.WriteLine($"Total inventario: {totalInventario:C}");

        // 4. Usar estructuras de control
        if (miTeclado is IVendible vendible)
        {
            Console.WriteLine($"Precio final con IVA: {vendible.CalcularPrecioFinal():C}");
        }
    }
}
Console.ReadKey();
    }
    
}