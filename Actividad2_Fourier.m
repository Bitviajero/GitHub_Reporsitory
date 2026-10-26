%======================================================================
%---ACTIVIDAD FORMATIVA 2: TRANSFORMADA DE FOURIER.---
%Ingeniero: Alfonso Rios Belmares
%Descripcion: Calculo y graficacion del espectro de magnitud de señales
%======================================================================

% 1. LIMPIEZA Y PREPARACION (Buena practica)
clear; clc; close all;

% 2. DEFINICION DE SEÑALES
t=-5:0.01:5;

u = t >= 0; %Funcion de escalon unitario

pulso = (t >= -1) & (t <= 1); %Funcion del pulso rectangular

x = 1 * cos((2 * pi*t)+ 0); %Funcion Senoidal

pulso_desp = (t >= 0) & (t <= 2);

%pulso_comp = (t >= -0.5) & (t <=0.5);

% 3. PARAMETROS PARA LA FFT
Fs = 1/0.01;
N=length(t);
f = (-N/2 : N/2-1) * (Fs/N);

% 4. CALCULO DE LA TRANSFORMADA DE FOURIER Y MAGNITUD

U_fft = fftshift(fft(u));
P_fft = fftshift(fft(pulso));
X_fft = fftshift(fft(x));
P_desp_fft = fftshift(fft(pulso_desp));



mag_U = abs(U_fft);
mag_P = abs(P_fft);
mag_X = abs(X_fft);
mag_P_desp = abs(P_desp_fft);


% 5. VISUALIZACION DEL DOMINIO DEL TIEMPO


figure(1);

subplot(3,1,1);  
plot(t,u);
title('Función Escalón Unitario u(t)');
xlabel('Tiempo t (s)'); 
grid on;

subplot(3,1,2);
plot(t,pulso);
title('Pulso Rectangular p_\tau(t)');
xlabel ('Tiempo t (s)');
grid on;

subplot(3,1,3);
plot(t,x);
title('Señal Senoidal x(t)');
xlabel('Tiempo t (s)');
grid on;

% 6. VISUALIZACION DE LA FRECUENCIA (FFT)

figure(2)

subplot(3,1,1);
plot(f,mag_U, 'LineWidth', 1.5);
title('Espectro de Magnitud de u(t)');
xlabel('Frecuencia (Hz)');
ylabel('|U(f)|');
grid on;

subplot(3,1,2);
plot(f,mag_P, 'LineWidth', 1.5);
title('Espectro de Magnitud de p_\tau(t)');
xlabel('Frecuencia (Hz)');ylabel('|P(f)|');
grid on;

subplot(3,1,3);
plot(f,mag_X, 'LineWidth', 1.5);
title('Espectro de Magnitud de x(t)');
xlabel('Frecuencia (Hz)');ylabel('|X(f)|');
grid on;

figure(3)
subplot(1,1,1)
plot(f,mag_P_desp, 'LineWidth', 1.5);
title('Grafica de desplazamiento');
xlabel('Frecuencia (Hz)');
hold on;
plot(f,mag_P, 'r--', 'LineWidth', 1.5');
legend('Pulso desplazado', 'Pulso original');
ylim([0 30]);


% 7. PROPIEDAD DE ESCALAMIENTO EN EL TIEMPO


% Pulso más angosto (de -0.5 a 0.5, duración = 1)
pulso_comp = (t >= -0.5) & (t <= 0.5); 

% Calculamos su FFT y magnitud
P_comp_fft = fftshift(fft(pulso_comp));
mag_P_comp = abs(P_comp_fft);

% Graficamos en una nueva figura para comparar
figure(4);
plot(f, mag_P, 'LineWidth', 1.5); hold on;   % Pulso original (ancho 2) en azul
plot(f, mag_P_comp, 'r', 'LineWidth', 1.5);  % Pulso comprimido (ancho 1) en rojo

title('Propiedad de Escalamiento: Tiempo vs Frecuencia');
xlabel('Frecuencia (Hz)'); 
ylabel('Magnitud');
legend('Pulso Original (ancho 2)', 'Pulso Comprimido (ancho 1)');
ylim([0 30]); % Recorte del eje Y
grid on;