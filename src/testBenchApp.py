# =====================================
# NOMBRE: Ruben Sahuquillo Redondo
# ASIGNATURA: Lenguajes de Alto Nivel para Aplicaciones Industriales
# DESCRIPCION: Interfaz aplicacion web, callbacks asociados a elementos web y su gestion¡¡. Uso de la libreria TestBench
# =====================================


# ----- LIBRERIAS ----- #
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import json
from lib.TestBech import TestBench


# ----- MQTT CONFIGURACION ----- #
topicReceive = "esp32/output"
topicSend = "esp32/input"
broker_IP = "10.74.94.63"
broker_PORT = 1883
mosquitto_path = r"C:\\Program Files\\mosquitto\\mosquitto.exe"
mosquitto_conf = r"C:\\Program Files\\mosquitto\\mosquitto.conf"


# ----- INSTANCIA TESTBENCH ----- #
tb = TestBench()
# Metodo para configurar broker MQTT
tb.configMQTTBroker(broker_IP, broker_PORT, mosquitto_path, mosquitto_conf)
# Metodo para configurar comunicacion MQTT
tb.configMQTT(topicSend=topicSend, topicReceive=topicReceive)


# ----- APP DASH ----- #
app = Dash(__name__)
app.title = "Banco de Pruebas"


# ----- ESTILOS CSS ----- #
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

title_style = {"color": "#003366", "marginBottom": "10px"}

button_style = {
    "backgroundColor": "#0066cc",
    "color": "white",
    "border": "none",
    "padding": "8px 16px",
    "borderRadius": "5px",
    "cursor": "pointer",
    "margin": "5px"
}

# ----- FUNCION AUXILIAR PARA ENVIAR MENSAJES MQTT ----- #
def send_action(action, data=None):
    payload = {"action": action}
    if data:
        payload["data"] = data
    tb.sendMQTT(tb.topicSend, json.dumps(payload))


# ----- INTERFAZ ----- #
app.layout = html.Div(style=main_style, children=[
    html.H1("Banco de Pruebas", style=title_style),
    html.Div(style=card_style, children=[
        html.H3("Parámetros de la hélice", style=title_style),
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                 children=[html.Div([html.Label("Modelo"), dcc.Input(id="propName", type="text")]),
                           html.Div([html.Label("Paso (in)"), dcc.Input(id="pitch", type="number")]),
                           html.Div([html.Label("Diámetro (in)"), dcc.Input(id="diameter", type="number")]),
                        ]
                )
    ]),
    html.Div(style=card_style, children=[
        html.H3("Parámetros del motor", style=title_style),
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                 children=[html.Div([html.Label("Modelo"), dcc.Input(id="motorName", type="text")]),
                           html.Div([html.Label("Voltaje (V)"), dcc.Input(id="voltage", type="number")]),
                           html.Div([html.Label("KV"), dcc.Input(id="kv", type="number")]),
                           html.Div([html.Label("Corriente Máx (A)"), dcc.Input(id="maxCurrent", type="number")]),
                        ]
                )
    ]),
    html.Div(style=card_style, children=[
        html.H3("Parámetros del ensayo", style=title_style),
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                 children=[html.Div([html.Label("Nombre del ensayo"), dcc.Input(id="testName", type="text")]),
                           html.Div([html.Label("Número de pasos"), dcc.Input(id="step", type="number")]),
                           html.Div([html.Label("Velocidad inicio (%)"), dcc.Input(id="vel_init", type="number")]),
                           html.Div([html.Label("Duración por paso (s)"), dcc.Input(id="stepTime", type="number")]),
                           html.Div([html.Label("Velocidad final (%)"), dcc.Input(id="vel_last", type="number")]),
                           html.Div([html.Label("Número de vueltas"), dcc.Input(id="cicles", type="number")]),
                        ]
                ),
        html.H4("Variables a medir", style={"marginTop": "20px"}),
        dcc.Checklist(id="measure_flags",
                      options=[{"label": "RPM", "value": "measure_rpm"},
                               {"label": "Empuje", "value": "measure_thrust"},
                               {"label": "Par", "value": "measure_torque"},
                               {"label": "Corriente", "value": "measure_current"}
                            ],
                      style={"marginLeft": "10px", "marginTop": "10px"}
                    ),
        html.Div(id="output", style={"display": "none"})
    ]),
    html.Div(style=card_style, children=[
        html.H3("Celdas de carga", style=title_style),
        html.Div(style={"display": "flex", "justifyContent": "space-evenly"},
                 children=[html.Div([html.H4("Tarar"),html.Button("Tarar", id="tare", style=button_style)]),
                           html.Div([html.H4("Calibrar"),
                                     html.Div([html.Label("Peso (g)"), dcc.Input(id="weight", type="number")]),
                                     html.Button("Calibrar", id="calibrate", style=button_style)
                            ])
        ])
    ]),
    html.Div(style=card_style, children=[html.Button("Iniciar Ensayo", id="start", style=button_style),
                                         html.Button("Detener Ensayo", id="stop", style={**button_style, "backgroundColor": "#cc0000"})
    ]),
    html.Div(style=card_style, children=[html.H3("Datos en tiempo real", style=title_style),
                                         dcc.Graph(id="live-graph"),
                                         dcc.Interval(id="interval-update", interval=1000)
    ])
])


# ----- CALLBACKS ----- #
@app.callback(
    Output("output", "children"),
    Input("start", "n_clicks"),
    [Input("vel_init", "value"),
     Input("vel_last", "value"),
     Input("stepTime", "value"),
     Input("step", "value"),
     Input("cicles", "value"),
     Input("measure_flags", "value"),
     Input("propName", "value"),
     Input("pitch", "value"),
     Input("diameter", "value"),
     Input("motorName", "value"),
     Input("kv", "value"),
     Input("maxCurrent", "value"),
    ]
)
def start_test(n, vel_init, vel_last, stepTime, step, cicles, measure_flags, propeller, pitch, diameter, motor, kv, max_current):
    """
    :param n: Clicks en boton start
    :param vel_init: Velocidad (%) de inicio del test
    :param vel_last: Velocidad (%) de finalizacion del test
    :param stepTime: Tiempo entre pasos
    :param step: Tamaño de paso entre porcentajes
    :param cicles: Numero de ciclos a realizar
    :param measure_flags: Mediciones a realizar
    :param propeller: Nombre o fabricante de la hélice
    :param pitch: Pitch de la helice
    :param diameter: Diametro de la heñice
    :param motor: Nombre o fabricante del motor
    :param kv: KV del motor
    :param max_current: Corriente maxima admisible por el motor
    """
    # Si no hay clicks, no devolver nada
    if not n:
        return

    # Limpiar listas de mediciones y parametros calculados
    tb._pct.clear()
    tb._speeds.clear()
    tb._thrusts.clear()
    tb._torques.clear()
    tb._currents.clear()
    tb._potencia_electrica.clear()
    tb._potencia_mecanica.clear()
    tb._rendimiento.clear()
    tb._Kt.clear()
    tb._Kv.clear()

    # Diccionario con parametros de configuracion del ensayo
    config = {"vel_init": vel_init,
              "vel_last": vel_last,
              "stepTime": stepTime,
              "step": step,
              "cicles": cicles,
              "max_current": max_current,
              "measure_rpm": "measure_rpm" in (measure_flags or []),
              "measure_thrust": "measure_thrust" in (measure_flags or []),
              "measure_torque": "measure_torque" in (measure_flags or []),
              "measure_current": "measure_current" in (measure_flags or []),
            }
    # Metodo para setear informacion acerca del ensayo
    tb.setTestInfo(propeller, pitch, diameter, motor, kv, max_current)
    # Metodo para introducir parametros del ensayo
    tb.setTestConfig(config)
    # Metodo para enviar accion y datos al banco de pruebas
    send_action("start", config)
    print("Ensayo iniciado")


@app.callback(Input("stop", "n_clicks"))
def stop_test(n):
    """
    :param n: Cicks en stop
    """
    # Si ha habido click, enviar accion de stop
    if n:
        send_action("stop")


@app.callback(Input("tare", "n_clicks"))
def tare(n):
    """
    :param n: Clicks en tare
    """
    # Si ha habido click, enviar accion de tare
    if n:
        send_action("tare")


@app.callback(Input("calibrate", "n_clicks"), Input("weight", "value"))
def cal(n, weight):
    """
    :param n: Clicks en calibrate
    :param weight: Peso introducido para calibracion
    """
    # Diccionario con peso de calibracion para mantener formato
    config = {
        "weight": weight
    }
    # Si ha habido click, enviar accion y datos de calibrate
    if n:
        send_action("calibrate", config)


@app.callback(
    Output("live-graph", "figure"),
    Input("interval-update", "n_intervals")
)
def update_graph(n):
    """
    :param n: Intervalo de actualizacion
    """
    # Si no existe porcentaje seteado, esperar datos (mostrar mensaje en grafico)
    if not tb._pct:
        return px.line(title="Esperando datos...")
    # Crear figura de grafico de linea con listas de mediciones
    fig = px.line(x=tb._pct,
                  y=[tb._thrusts, tb._torques, tb._currents],
                  labels={"x": "Velocidad (%)", "value": "Magnitud"},
                  title="Variables vs Velocidad"
    )
    # Nombrar / titular curvas
    fig.data[0].name = "Empuje"
    fig.data[1].name = "Par"
    fig.data[2].name = "Corriente"
    # Devolver figura
    return fig


# ----- MAIN ----- #
# Si el programa se ejecuta desde este archivo con este nombre, iniciar aplicacion Dash
if __name__ == "__main__":
    app.run(debug=False)
