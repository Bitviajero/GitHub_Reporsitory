using System;

public class Animal
{
    // Atributos
    protected string nombre;
    protected int edad;

    // Constructor
    public Animal(string nombre, int edad)
    {
        this.nombre = nombre;
        this.edad = edad;
    }

    // Métodos
    public void Comer()
    {
        Console.WriteLine($"{nombre} está comiendo.");
    }

    public void Dormir()
    {
        Console.WriteLine($"{nombre} está durmiendo.");
    }
}

public class Perro : Animal
{
    private string raza;
    
    public Perro(string nombre, int edad, string raza)
        : base(nombre, edad)
    {
        this.raza = raza;
    }

    public void Informacion()
    {
        Console.WriteLine($"{nombre} tiene {edad} años y es un {raza}.");
    }
}

class Program
{
    static void Main(string[] args)
    {
        Perro perro = new Perro("Firulais", 5, "Golden Retriever");

        perro.Comer();
        perro.Dormir();
        perro.Informacion();
    }
}

