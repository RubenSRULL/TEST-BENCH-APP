# Banco de Pruebas para Motores Eléctricos con ESP32

## Descripción general

Este proyecto implementa un **banco de pruebas automatizado para motores eléctricos con hélice**, permitiendo la medición y visualización en tiempo real de **velocidad de rotación (RPM), empuje, par y consumo de corriente**.

El sistema está compuesto por:
- Un **microcontrolador ESP32** encargado del control del motor y la adquisición de sensores.
- Un **broker MQTT** para la comunicación.
- Una **aplicación web desarrollada con Dash (Python)** que actúa como interfaz de usuario (HMI).

---

## Arquitectura del sistema

Arquitectura cliente-servidor basada en MQTT:

- ESP32 → Publica datos de sensores
- Dash App → Envía comandos y visualiza resultados
- Mosquitto → Broker MQTT intermedio

---

## Características principales

- Control de velocidad del motor por PWM  
- Ensayo automático por pasos configurables  
- Medición de:
  - RPM
  - Empuje (celda de carga)
  - Par (celda de carga)
  - Corriente eléctrica
- Visualización gráfica en tiempo real  
- Interfaz web intuitiva  
- Comunicación inalámbrica vía WiFi + MQTT  
- Sistema basado en máquina de estados  

---

## Hardware utilizado

- ESP32  
- Módulo HX711 (x2)  
- Celdas de carga (x2 empuje y par)  
- Sensor de corriente ACS712  
- Tacómetro  
- Controlador ESC  
- Motor brushless + hélice  
- Fuente de alimentación +12 V

---

## Software utilizado

### ESP32
- Arduino IDE / PlatformIO
- Librerías:
  - `HX711`
  - `WiFi`
  - `ArduinoJson`
  - `PubSubClient`

### Aplicación de usuario
- Python 3.10+
- Librerías:
  - `dash`
  - `plotly`
  - `paho-mqtt`

### Comunicación
- Mosquitto MQTT Broker

---