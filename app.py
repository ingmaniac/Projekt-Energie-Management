import gradio as gr
import numpy as np
import matplotlib.pyplot as plt

def simulate_temp(alpha, o, c, m, t_start, t_soll, heizkurve, k, nachtmodus):
    t_umgebung = 10 + 5 * np.sin(np.linspace(0, 2 * np.pi, 1440))
    T = t_start
    temperaturen = []

    for minute in range(1440):
        T_umg = t_umgebung[minute]
        stunde = minute // 60

        if nachtmodus == "Nachtabschaltung" and (stunde < 6 or stunde >= 22):
            P_v_dyn = 0
        else:
            T_soll_local = t_soll
            if nachtmodus == "Nachtabsenkung" and (stunde < 6 or stunde >= 22):
                T_soll_local -= 3
            T_vorlauf = heizkurve * max(T_soll_local - T_umg, 0)
            P_v_dyn = k * max(T_vorlauf - T, 0)

        dT_dt = (P_v_dyn - alpha * o * (T - T_umg)) / (c * m)
        T += dT_dt * 60
        temperaturen.append(T)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(np.linspace(0, 24, 1440), temperaturen, label="Raumtemperatur")
    ax.plot(np.linspace(0, 24, 1440), t_umgebung, label="Außentemperatur", linestyle="--")
    ax.set_xlabel("Uhrzeit (h)")
    ax.set_ylabel("Temperatur (°C)")
    ax.set_title("Temperaturverlauf über 24h")
    ax.grid(True)
    ax.legend()
    
    return fig

iface = gr.Interface(
    fn=simulate_temp,
    inputs=[
        gr.Number(5, label="Wärmeübergangskoeffizient alpha [W/m²·K]"),
        gr.Number(70, label="Oberfläche O [m²]"),
        gr.Number(1010, label="Wärmekapazität c [J/kg·K]"),
        gr.Number(1000, label="Masse m [kg]"),
        gr.Number(20, label="Starttemperatur T_start [°C]"),
        gr.Number(21, label="Solltemperatur T_soll [°C]"),
        gr.Number(1.5, label="Heizkurven-Steigung"),
        gr.Number(1500, label="Heizleistung pro Grad k"),
        gr.Radio(["Keine Absenkung", "Nachtabsenkung", "Nachtabschaltung"], label="Nachtbetrieb")
    ],
    outputs=gr.Plot(),
    title="Temperatur Simulation mit Heizkurve",
    description="Simuliere den Temperaturverlauf eines Raumes über 24 Stunden."
)

if __name__ == "__main__":
    iface.launch()
