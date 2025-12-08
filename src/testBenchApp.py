#----- LIBRARIES -----#
from dash import Dash, dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import paho.mqtt.client as mqtt
import subprocess
import time
import json
import os


#----- VARIABLES -----#
topicReceive = "esp32/output"
topicSend = "esp32/input"
broker_IP = "10.251.249.63"
broker_PORT = 1883
mosquitto_path = r"C:\Program Files\mosquitto\mosquitto.exe"
mosquitto_conf = r"C:\Program Files\mosquitto\mosquitto.conf"
latest_data = {"velocity": [], "thrust": [], "torque": [], "current": []}
porcentaje, velocidad, empuje, par, corriente = [], [], [], [], []
client = None

#----- FUNCIONES MQTT -----#
def iniciar_broker():
    try:
        if not any("mosquitto" in p for p in os.popen('tasklist').read().splitlines()):
            subprocess.Popen(
                f'"{mosquitto_path}" -v -c "{mosquitto_conf}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("Broker Mosquitto iniciado en segundo plano.")
            time.sleep(3)
        else:
            print("Broker Mosquitto ya en ejecución.")
    except Exception as e:
        print(f"Error al iniciar el broker: {e}")


def iniciar_mqtt():
    global client
    if client is None:
        try:
            iniciar_broker()
            client = mqtt.Client(
                protocol=mqtt.MQTTv5,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            client.on_message = on_message
            client.connect(broker_IP, broker_PORT)
            client.subscribe(topicReceive)
            client.loop_start()
            print("Cliente MQTT conectado.")
        except Exception as e:
            print(f"Error al conectar MQTT: {e}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        #{"velocity": 1000, "thrust": 5, "torque": 0.3, "current": 2}
        latest_data["velocity"].append(data.get("velocity", 0))
        latest_data["thrust"].append(data.get("thrust", 0))
        latest_data["torque"].append(data.get("torque", 0))
        latest_data["current"].append(data.get("current", 0))
        print("Datos recibidos:\n")
        print(f"Velocidad -> {data.get("velocity", 0)}")
        print(f"Empuje -> {data.get("thrust", 0)}")
        print(f"Torque -> {data.get("torque", 0)}")
        print(f"Corriente -> {data.get("current", 0)}")
    except Exception as e:
        print(f"Error parsing MQTT message: {e}")



#----- APP DASH -----#
app = Dash(__name__)


#----- CSS STYLES -----#
main_style = {
    "fontFamily": "Arial, sans-serif",
    "backgroundColor": "#f5f7fa",
    "padding": "20px"
}

card_style = {
    "backgroundColor": "white",
    "padding": "20px",
    "marginBottom": "20px",
    "borderRadius": "10px",
    "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"
}

title_style = {
    "color": "#003366", 
    "marginBottom": "10px"
}

button_style = {
    "backgroundColor": "#0066cc",
    "color": "white",
    "border": "none",
    "padding": "8px 16px",
    "borderRadius": "5px",
    "cursor": "pointer",
    "margin": "5px"
}

display_box = {
    "backgroundColor": "#e6f0ff",
    "border": "1px solid #b3c6ff",
    "borderRadius": "8px",
    "padding": "10px 20px",
    "textAlign": "center",
    "flex": "1"
}

#----- LAYOUT -----#
app.layout = html.Div(style=main_style, children=[
    
    html.H1("Banco de Pruebas", style=title_style),

    html.Div(style=card_style, children=[
        html.H3("Parámetros de la hélice", style=title_style),

        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"}, children=[
            html.Div([
                html.Label("Modelo"),
                dcc.Input(id="propName", type="text", style={"width": "150px"})
            ]),

            html.Div([
                html.Label("Paso (in)"),
                dcc.Input(id="pitch", type="number", style={"width": "150px"})
            ]),

            html.Div([
                html.Label("Diámetro (in)"),
                dcc.Input(id="diameter", type="number", style={"width": "150px"})
            ])
        ])
    ]),

    html.Div(style=card_style, children=[
        html.H3("Parámetros del motor", style=title_style),

        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"}, children=[
            html.Div([
                html.Label("Modelo"),
                dcc.Input(id="motorName", type="text", style={"width": "150px"})
            ]),

            html.Div([
                html.Label("Voltaje (V)"),
                dcc.Input(id="voltage", type="number", style={"width": "150px"})
            ]),

            html.Div([
                html.Label("KV"),
                dcc.Input(id="kv", type="number", style={"width": "150px"})
            ]),
            
            html.Div([
                html.Label("Corriente máx (A)"),
                dcc.Input(id="maxCurrent", type="number", style={"width": "150px"})
            ])
        ])
    ]),

    html.Div(style=card_style, children=[
        html.H3("Parámetros del ensayo", style=title_style),

        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"}, children=[

            html.Div([
                html.Label("Nombre del ensayo"),
                dcc.Input(id="testName", type="text", style={"width": "150px"})
            ]),

            html.Div([
                html.Label("Número de pasos"),
                dcc.Input(id="step", type="number", style={"width": "150px"})
            ]),

            html.Div([
                html.Label("Velocidad inicio (%)"),
                dcc.Input(id="vel_init", type="number", style={"width": "150px"})
            ]),


            html.Div([
                html.Label("Duración por paso (s)"),
                dcc.Input(id="stepTime", type="number", step=0.1, style={"width": "150px"})
            ]),

            html.Div([
                html.Label("Velocidad final (%)"),
                dcc.Input(id="vel_last", type="number", style={"width": "150px"})
            ]),


            html.Div([
                html.Label("Número de vueltas"),
                dcc.Input(id="cicles", type="number", style={"width": "150px"})
            ])
        ]),

        html.H4("Variables a medir", style={"marginTop": "20px"}),

        dcc.Checklist(
            id="measure_flags",
            options=[
                {"label": "RPM", "value": "measure_rpm"},
                {"label": "Empuje", "value": "measure_thrust"},
                {"label": "Par", "value": "measure_torque"},
                {"label": "Corriente", "value": "measure_current"}
            ],
            style={"marginLeft": "10px", "marginTop": "10px"}
        )
    ]),

    html.Div(style=card_style, children=[
        html.H3("Celdas de carga", style=title_style),

        html.Div(style={"display": "flex", "justifyContent": "space-around"}, children=[

            html.Div(children=[
                html.H4("Empuje"),
                html.Button("Tarar", id="tare1", style=button_style),
                html.Button("Calibrar", id="calibrate1", style=button_style)
            ]),

            html.Div(children=[
                html.H4("Par"),
                html.Button("Tarar", id="tare2", style=button_style),
                html.Button("Calibrar", id="calibrate2", style=button_style)
            ])
        ])
    ]),

    html.Div(style=card_style, children=[
        html.Button("Iniciar Ensayo", id="start", style=button_style),
        html.Button("Detener Ensayo", id="stop",
                    style={**button_style, "backgroundColor": "#cc0000"})
    ]),

    html.Div(style=card_style, children=[
        html.H3("Gráfico de variables vs Velocidad", style=title_style),
        dcc.Graph(id="live-graph"),
        dcc.Interval(
            id="interval-update",
            interval=1000,
            n_intervals=0
        )
    ])
])



#----- CALLBACKS -----#
@app.callback(
    Input("start", "n_clicks"),
    [
        Input("propName", "value"),
        Input("diameter", "value"),
        Input("pitch", "value"),
        Input("motorName", "value"),
        Input("kv", "value"),
        Input("voltage", "value"),
        Input("maxCurrent", "value"),
        Input("testName", "value"),
        Input("vel_init", "value"),
        Input("vel_last", "value"),
        Input("stepTime", "value"),
        Input("step", "value"),
        Input("cicles", "value"),
        Input("measure_flags", "value")
    ]
)
def startTest(start_clicks,
                     propName, diameter, pitch,
                     motorName, kv, voltage, maxCurrent,
                     testName, vel_init, vel_last, stepTime, step, cicles,
                     measure_flags):
    if not start_clicks:
        return "Esperando para iniciar ensayo..."
    
    else:
        test_data = {
            "Helice": {
                "Modelo": propName,
                "Diámetro (in)": diameter,
                "Paso (in)": pitch
            },
            "Motor": {
                "Modelo": motorName,
                "KV": kv,
                "Voltaje (V)": voltage,
                "Corriente Máx (A)": maxCurrent
            },
            "Ensayo": {
                "Nombre": testName,
                "Velocidad inicio": vel_init,
                "Velocidad final": vel_last,
                "Duracion por paso": stepTime,
                "Pasos": step,
                "Vueltas": cicles,
                "Variables medidas": measure_flags
            }
        }
        payload = json.dumps({
            "action": "start",
            "data": {
                "vel_init": vel_init,
                "vel_last": vel_last,
                "stepTime": stepTime,
                "step": step,
                "cicles": cicles,
                "measure_rpm": "measure_rpm" in measure_flags,
                "measure_thrust": "measure_thrust" in measure_flags,
                "measure_torque": "measure_torque" in measure_flags,
                "measure_current": "measure_current" in measure_flags
            }
        }, indent=4)

        client.publish(topicSend, payload)
        print(f"→ MQTT enviado: {payload}")


@app.callback(
    Input("stop", "n_clicks")
)
def stopTest(clicks):
    print("STOP TEST")
    payload = json.dumps({
        "action": "stop",
    }, indent=4)
    client.publish(topicSend, payload)

@app.callback(
    Input("tare1", "n_clicks")
)
def tare(clicks):
    print("Tare 1")
    payload = json.dumps({
        "action": "tare1",
    }, indent=4)
    client.publish(topicSend, payload)

@app.callback(
    Input("tare2", "n_clicks")
)
def tare(clicks):
    print("Tare 2")
    payload = json.dumps({
        "action": "tare2",
    }, indent=4)
    client.publish(topicSend, payload)

@app.callback(
    Input("calibrate1", "n_clicks")
)
def calibrate(clicks):
    print("Calibrate 1")
    payload = json.dumps({
        "action": "calibrate1",
    }, indent=4)
    client.publish(topicSend, payload)

@app.callback(
    Input("calibrate2", "n_clicks")
)
def calibrate(clicks):
    print("Calibrate 2")
    payload = json.dumps({
        "action": "calibrate2",
    }, indent=4)
    client.publish(topicSend, payload)



@app.callback(
    Output("live-graph", "figure"),
    Input("interval-update", "n_intervals")
)
def update_graph(n):
    if not latest_data["velocity"]:
        return px.line(title="Esperando datos...")
    fig = px.line(
        x=latest_data["velocity"],
        y=[latest_data["thrust"], latest_data["torque"], latest_data["current"]],
        labels={"x": "Velocidad (%)", "y": "Valor"},
        title="Variables vs Velocidad"
    )
    fig.data[0].name = "Empuje"
    fig.data[1].name = "Par"
    fig.data[2].name = "Corriente"
    return fig


#----- MAIN -----#
if __name__ == '__main__':
    iniciar_mqtt()
    app.run(debug=False)