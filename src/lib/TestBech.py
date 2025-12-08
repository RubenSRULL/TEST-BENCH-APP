#################################
#NAME: Ruben Sahuquillo Redondo
#SIGNATURE: Sistemas Embebidos
#PROYECTO FINAL
#################################


#----- LIBRERIAS -----#
import paho.mqtt.client as mqtt
import subprocess
import time
import json
import os
import csv
import math
import matplotlib.pyplot as plt


#----- CLASE -----#
class TestBench:
    #CONSTRUCTOR
    def __init__(self):
        self._pct = []
        self._speeds = []
        self._thrusts = []
        self._torques = []
        self._currents = []
        self._voltages = []

        self._client = None
        self.topicReceive = None
        self.topicSend = None
        self._brokerIP = None
        self._brokerPORT = None

        self._Kt = None
        self._Kv = None
        self._potencia_electrica = None
        self._potencia_mecanica = None
        self._rendimiento = None

        self._config = None

        self._config = {}

        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.fig_path  = os.path.join(base_path, "fig")
        self.log_path  = os.path.join(base_path, "logs")

        os.makedirs(self.fig_path, exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)


    #CONFIGURAR BROKER MQTT
    def configMQTTBroker(self, broker_ip, broker_port, 
                            mosquitto_path = r"C:\Program Files\mosquitto\mosquitto.exe",
                            mosquitto_conf = r"C:\Program Files\mosquitto\mosquitto.conf"):
            """Inicializa el broker MQTT si no está inicializado"""
            self._brokerIP = str(broker_ip)
            self._brokerPORT = int(broker_port)

            try:
                if not any("mosquitto" in p for p in os.popen('tasklist').read().splitlines()):
                    subprocess.Popen(f'"{mosquitto_path}" -v -c "{mosquitto_conf}"',
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                    )
                    print("Broker Mosquitto iniciado en segundo plano.")
                    time.sleep(2)
                else:
                    print("Broker Mosquitto en ejecución.")

            except Exception as e:
                print(f"Error al iniciar el broker: {e}")


    #CONFIGURAR MQTT
    def configMQTT(self, topicSend, topicReceive):
        """Configura la conexión MQTT y se realiza la subscripción a los tópicos indicados"""
        self.topicSend = topicSend
        self.topicReceive = topicReceive

        if self._brokerIP is None or self._brokerPORT is None:
            raise ValueError("Debe configurar primero el broker con configMQTTBroker()")
        
        else:
            if self._client is None:
                try:
                    self._client = mqtt.Client()
                    self._client.on_message = self.receiveMQTT
                    self._client.connect(self._brokerIP, self._brokerPORT)
                    self._client.subscribe(topicReceive)
                    self._client.loop_start()
                    print("\nCliente MQTT conectado\n")
                    print(f"Publica en Tópico -> {topicSend}\n")
                    print(f"Recibe en Tópico -> {topicReceive}")

                except Exception as e:
                    print(f"Error al conectar MQTT: {e}")


    #ENVIAR MQTT
    def sendMQTT(self, topicSend, msg):
        if self._client is None:
            print("Error: cliente MQTT no inicializado.")
            return
            
        try:
            self._client.publish(topicSend, msg)

        except Exception as e:
            print(f"No se pudo enviar MQTT: {e}")


    #RECIBIR MQTT
    def receiveMQTT(self, client, userdata, msg):
        try:
            payload = msg.payload.decode().strip()

            if not payload:
                print("Mensaje MQTT vacío recibido.")
                return

            data = json.loads(payload)

            # Validar que data sea un diccionario
            if not isinstance(data, dict):
                print(f"Mensaje MQTT no válido (no es un dict JSON): {payload}")
                return
            
            print(data)

            pct = round(data.get("%", 0.0), 2)
            rpm = round(data.get("RPM", 0.0), 2)
            empuje = round(data.get("Empuje", 0.0), 2)
            par = round(data.get("Par", 0.0), 2)
            intensidad = round(data.get("Intensidad", 0.0), 2)
            voltaje = round(data.get("Voltaje", 0.0), 2)

            self._pct.append(pct)
            self._speeds.append(rpm)
            self._thrusts.append(empuje)
            self._torques.append(par)
            self._currents.append(intensidad)
            self._voltages.append(voltaje)

            vel_last = self._config.get("vel_last") if self._config else None

            if vel_last is not None and pct >= vel_last:
                self.finish()

        except json.JSONDecodeError:
            print(f"JSON inválido recibido: {payload}")
        except Exception as e:
            print(f"Error al recibir datos MQTT: {e}")




    #FINALIZAR ENSAYO
    def finish(self, name="testbench_result"):
        """Genera automáticamente informe y figura al finalizar el test."""
        print("\nGenerando informe CSV y figuras...")

        self._Kt, self._Kv, self._rendimiento, self._potencia_electrica, self._potencia_mecanica = self.computeParameters()

        self.reportGenerate(name)

        self.figureGenerate(name)

        print(f"Informe generado en: {self.log_path}")
        print(f"Gráficas generadas en: {self.fig_path}")
        print("\nProceso finalizado.")
        self.disconnect()


    #DESCONECTAR MQTT
    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            print("MQTT desconectado.")


    #CALCULAR PARÁMETROS ENSAYO
    def computeParameters(self):
        """Realiza el cálculo de los parámetros del motor"""
        Kt = Kv = rendimiento = 0

        if not self._currents or not self._voltages or not self._thrusts or not self._torques or not self._pct or not self._speeds:
            return Kt, Kv, rendimiento, [], []
        
        else:
            Kt = []

            for torque, current in zip(self._torques, self._currents):
                if current != 0:
                    Kt.append(torque / current)
                else:

                    Kt.append(0)
            Kt = sum(Kt) / len(Kt)

            Kv = []
            for speed, voltage in zip(self._speeds, self._voltages):
                if voltage != 0:
                    Kv.append(speed / voltage)
                else:
                    Kv.append(0)
            Kv = sum(Kv) / len(Kv)

            potencia_electrica = []
            for current, voltage in zip(self._currents, self._voltages):
                potencia_electrica.append(voltage * current)

            potencia_mecanica = []
            for speed, torque in zip(self._speeds, self._torques):
                omega = speed * 2 * math.pi / 60
                potencia_mecanica.append(torque * omega)

            rendimiento = []
            for pe, pm in zip(potencia_electrica, potencia_mecanica):
                if pe != 0:
                    rendimiento.append(pm / pe)
                else:
                    rendimiento.append(0)
            
            rendimiento = sum(rendimiento) / len(rendimiento)

        return Kt, Kv, rendimiento, potencia_electrica, potencia_mecanica


    #GENERAR INFORME
    def reportGenerate(self, filename):
        """Genera un informe .csv con los resultados del test"""

        fullpath = os.path.join(self.log_path, filename + '.csv')

        with open(fullpath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["%", "RPM", "Empuje", "Par", "Intensidad", "Voltaje"])

            for row in zip(self._pct, self._speeds, self._thrusts, self._torques, self._currents, self._voltages):
                writer.writerow(row)
            
            writer.writerow([])
            writer.writerow(["Kt", self._Kt])
            writer.writerow(["Kv", self._Kv])
            writer.writerow(["Potencia Eléctrica (W)"])
            writer.writerow(self._potencia_electrica)
            writer.writerow(["Potencia Mecánica (W)"])
            writer.writerow(self._potencia_mecanica)
            writer.writerow(["Rendimiento", self._rendimiento])


    #GENERAR FIGURAS
    def figureGenerate(self, name):
        """Genera gráficas con las curvas obtenidas en el ensayo"""

        if not self._pct:
            print("No hay datos registrados para generar figuras.")
            return

        fullpath = os.path.join(self.fig_path, name + ".png")

        fig, axs = plt.subplots(3, 2, figsize=(12, 14))
        fig.suptitle("Resultados del Test Bench", fontsize=16)

        axs[0, 0].plot(self._pct, self._speeds)
        axs[0, 0].set_title("RPM vs %")
        axs[0, 0].set_xlabel("%")
        axs[0, 0].set_ylabel("RPM")

        axs[0, 1].plot(self._pct, self._thrusts)
        axs[0, 1].set_title("Empuje vs %")
        axs[0, 1].set_xlabel("%")
        axs[0, 1].set_ylabel("Empuje (N)")

        axs[1, 0].plot(self._pct, self._torques)
        axs[1, 0].set_title("Par vs %")
        axs[1, 0].set_xlabel("%")
        axs[1, 0].set_ylabel("Par (Nm)")

        axs[1, 1].plot(self._pct, self._currents)
        axs[1, 1].set_title("Intensidad vs %")
        axs[1, 1].set_xlabel("%")
        axs[1, 1].set_ylabel("Intensidad (A)")

        axs[2, 0].plot(self._pct, self._voltages)
        axs[2, 0].set_title("Voltaje vs %")
        axs[2, 0].set_xlabel("%")
        axs[2, 0].set_ylabel("Voltaje (V)")

        plt.tight_layout()
        fig.savefig(fullpath, dpi=300)
        print("Figuras generadas")
        plt.close()


    #SET CONFIGRACIÓN TEST
    def setTestConfig(self, config):
        """Añade los paraámetros del test al atributo _config"""
        self._config = config


###############################
if __name__ == '__main__':
    tb = TestBench()
    tb.finish("resultado_final")