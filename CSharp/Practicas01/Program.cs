using System;

public class Animal
{
    // Atributos
    private string nombre;
    private int edad;

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

class Program
{
    static void Main(string[] args)
    {
        Animal animal = new Animal("Firulais", 5);

        animal.Comer();
        animal.Dormir();
    }
}
