# =====================================
# BANCO DE PRUEBAS - DASH + TESTBENCH
# Interfaz renovada estilo versión 2 pero usando TestBench
# =====================================

# ----- LIBRARIES ----- #
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import json
from lib.TestBech import TestBench

# ----- MQTT CONFIG ----- #
topicReceive = "esp32/output"
topicSend = "esp32/input"
broker_IP = "10.74.94.63"
broker_PORT = 1883
mosquitto_path = r"C:\\Program Files\\mosquitto\\mosquitto.exe"
mosquitto_conf = r"C:\\Program Files\\mosquitto\\mosquitto.conf"

# ----- TESTBENCH INSTANCE ----- #
tb = TestBench()

tb.configMQTTBroker(
    broker_IP,
    broker_PORT,
    mosquitto_path,
    mosquitto_conf
)

tb.configMQTT(
    topicSend=topicSend,
    topicReceive=topicReceive
)

# ----- APP DASH ----- #
app = Dash(__name__)
app.title = "Banco de Pruebas"

# ----- CSS STYLES ----- #
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

# ----- AUX MQTT SENDER USING TESTBENCH ----- #
def send_action(action, data=None):
    payload = {"action": action}
    if data:
        payload["data"] = data
    tb.sendMQTT(tb.topicSend, json.dumps(payload))


# ----- LAYOUT ----- #
app.layout = html.Div(style=main_style, children=[

    html.H1("Banco de Pruebas", style=title_style),

    html.Div(style=card_style, children=[
        html.H3("Parámetros de la hélice", style=title_style),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                html.Div([html.Label("Modelo"), dcc.Input(id="propName", type="text")]),
                html.Div([html.Label("Paso (in)"), dcc.Input(id="pitch", type="number")]),
                html.Div([html.Label("Diámetro (in)"), dcc.Input(id="diameter", type="number")]),
            ]
        )
    ]),

    html.Div(style=card_style, children=[
        html.H3("Parámetros del motor", style=title_style),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                html.Div([html.Label("Modelo"), dcc.Input(id="motorName", type="text")]),
                html.Div([html.Label("Voltaje (V)"), dcc.Input(id="voltage", type="number")]),
                html.Div([html.Label("KV"), dcc.Input(id="kv", type="number")]),
                html.Div([html.Label("Corriente Máx (A)"), dcc.Input(id="maxCurrent", type="number")]),
            ]
        )
    ]),

    html.Div(style=card_style, children=[
        html.H3("Parámetros del ensayo", style=title_style),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                html.Div([html.Label("Nombre del ensayo"), dcc.Input(id="testName", type="text")]),
                html.Div([html.Label("Número de pasos"), dcc.Input(id="step", type="number")]),
                html.Div([html.Label("Velocidad inicio (%)"), dcc.Input(id="vel_init", type="number")]),
                html.Div([html.Label("Duración por paso (s)"), dcc.Input(id="stepTime", type="number")]),
                html.Div([html.Label("Velocidad final (%)"), dcc.Input(id="vel_last", type="number")]),
                html.Div([html.Label("Número de vueltas"), dcc.Input(id="cicles", type="number")]),
            ]
        ),

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
        html.Div(style={"display": "flex", "justifyContent": "space-evenly"}, children=[
            html.Div([
                html.H4("Empuje"),
                html.Button("Tarar", id="tare1", style=button_style),
                html.Button("Calibrar", id="calibrate1", style=button_style)
            ]),
            html.Div([
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
        html.H3("Datos en tiempo real", style=title_style),
        dcc.Graph(id="live-graph"),
        dcc.Interval(id="interval-update", interval=1000)
    ])
])


# ----- CALLBACKS ----- #
@app.callback(
    Input("start", "n_clicks"),
    [
        Input("vel_init", "value"),
        Input("vel_last", "value"),
        Input("stepTime", "value"),
        Input("step", "value"),
        Input("cicles", "value"),
        Input("measure_flags", "value")
    ]
)
def start_test(n, vel_init, vel_last, stepTime, step, cicles, measure_flags):
    if not n:
        return

    # LIMPIAR DATOS DEL GRAFICO
    tb._pct.clear()
    tb._thrusts.clear()
    tb._torques.clear()
    tb._currents.clear()

    config = {
        "vel_init": vel_init,
        "vel_last": vel_last,
        "stepTime": stepTime,
        "step": step,
        "cicles": cicles,
        "measure_rpm": "measure_rpm" in (measure_flags or []),
        "measure_thrust": "measure_thrust" in (measure_flags or []),
        "measure_torque": "measure_torque" in (measure_flags or []),
        "measure_current": "measure_current" in (measure_flags or [])
    }

    tb.setTestConfig(config)
    send_action("start", config)
    print("Ensayo iniciado")



@app.callback(Input("stop", "n_clicks"))
def stop_test(n):
    if n:
        send_action("stop")


@app.callback(Input("tare1", "n_clicks"))
def tare1(n):
    if n:
        send_action("tare1")


@app.callback(Input("tare2", "n_clicks"))
def tare2(n):
    if n:
        send_action("tare2")


@app.callback(Input("calibrate1", "n_clicks"))
def cal1(n):
    if n:
        send_action("calibrate1")


@app.callback(Input("calibrate2", "n_clicks"))
def cal2(n):
    if n:
        send_action("calibrate2")


@app.callback(
    Output("live-graph", "figure"),
    Input("interval-update", "n_intervals")
)
def update_graph(n):
    if not tb._pct:
        return px.line(title="Esperando datos...")

    fig = px.line(
        x=tb._pct,
        y=[tb._thrusts, tb._torques, tb._currents],
        labels={"x": "Velocidad (%)", "value": "Magnitud"},
        title="Variables vs Velocidad"
    )

    fig.data[0].name = "Empuje"
    fig.data[1].name = "Par"
    fig.data[2].name = "Corriente"

    return fig


# ----- MAIN ----- #
if __name__ == "__main__":
    app.run(debug=False)
