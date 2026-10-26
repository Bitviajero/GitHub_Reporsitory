# Análisis de Señales y Transformada de Fourier en MATLAB

**Autor:** Alfonso Rios Belmares  
**Materia:** Señales y Sistemas  
**Fecha:** [Inserta la fecha de entrega]  

## 🎯 Objetivo
El propósito de este proyecto es simular y analizar señales elementales en el dominio del tiempo y su representación en el dominio de la frecuencia utilizando la Transformada Rápida de Fourier (FFT) en MATLAB. Asimismo, se verifican experimentalmente las propiedades de desplazamiento y escalamiento en el tiempo descritas en la teoría de Fourier.

## ️ Requisitos
- **Software:** MATLAB R2025b (o superior).
- **Conocimientos previos:** Conceptos básicos de señales de tiempo continuo y transformadas integrales.

## 📁 Estructura del Repositorio
- `Actividad2_Fourier.m`: Script principal de MATLAB que contiene la generación de señales, cálculo de la FFT y verificación de propiedades.
- `README.md`: Documentación del proyecto.

## 🚀 Instrucciones de Uso
1. Clonar o descargar este repositorio.
2. Abrir el archivo `Actividad2_Fourier.m` en MATLAB.
3. Ejecutar el script (presionando F5 o el botón "Run").
4. El código generará automáticamente 4 figuras:
   - **Figura 1:** Señales en el dominio del tiempo (Escalón, Pulso, Senoidal).
   - **Figura 2:** Espectro de magnitud (Dominio de la frecuencia).
   - **Figura 3:** Verificación de la propiedad de desplazamiento en el tiempo.
   - **Figura 4:** Verificación de la propiedad de escalamiento en el tiempo.

## 📚 Marco Teórico Breve
La Transformada de Fourier permite descomponer una señal en sus componentes de frecuencia. Mientras que en el dominio del tiempo observamos cómo cambia la señal, en el dominio de la frecuencia observamos qué frecuencias la componen y con qué magnitud. Este proyecto valida visualmente que comprimir una señal en el tiempo expande su espectro en frecuencia, y que desplazarla en el tiempo no altera su magnitud espectral.

## 📖 Referencias Bibliográficas
Kamen, E., & Heck, B. (2008). *Fundamentos de Señales y Sistemas* (3ra ed.). Editorial Pearson.