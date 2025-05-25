import sys
import os
import matplotlib.pyplot as plt
import tkinter
import tkinter.messagebox
import customtkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import filedialog
import pandas as pd
from datetime import datetime, timedelta, time
import matplotlib.dates as mdates

class NoCoordinatesToolbar(NavigationToolbar2Tk):
    def set_message(self, s):
        pass

    def zoom(self, *args):
        super().zoom(*args)
        for ax in self.canvas.figure.axes:
            ax._zoom_mode = 'x'

    def __init__(self, canvas, window):
        super().__init__(canvas, window)
        self._id_scroll = canvas.mpl_connect("scroll_event", self._on_scroll)
        self._id_press = canvas.mpl_connect("button_press_event", self._on_press)
        self._id_motion = canvas.mpl_connect("motion_notify_event", self._on_motion)
        self._id_release = canvas.mpl_connect("button_release_event", self._on_release)
        self._drag_start_x = None

    def _on_scroll(self, event):
        ax = self.canvas.figure.axes[0]
        if event.xdata is None:
            return
        cur_xlim = ax.get_xlim()
        x_center = event.xdata
        scale_factor = 1.1 if event.button == 'up' else 1 / 1.1
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        left = x_center - new_width / 2
        right = x_center + new_width / 2
        ax.set_xlim(left, right)
        self.canvas.draw_idle()

    def _on_press(self, event):
        if event.button == 1 and event.xdata is not None:
            self._drag_start_x = event.xdata

    def _on_motion(self, event):
        if self._drag_start_x is None or event.xdata is None:
            return
        dx = self._drag_start_x - event.xdata
        ax = self.canvas.figure.axes[0]
        cur_xlim = ax.get_xlim()
        ax.set_xlim(cur_xlim[0] + dx, cur_xlim[1] + dx)
        self.canvas.draw_idle()
        self._drag_start_x = event.xdata

    def _on_release(self, event):
        self._drag_start_x = None


class ReglerOptions(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.regler_typ = customtkinter.StringVar(value="PI")
        self.k_p = customtkinter.DoubleVar(value=2.7)
        self.k_i = customtkinter.DoubleVar(value=3.0)
        self.toleranz = customtkinter.DoubleVar(value=0.5)

        customtkinter.CTkLabel(self, text="Regler-Typ").pack(pady=(5, 0), padx=10, anchor="w")
        self.regler_auswahl = customtkinter.CTkComboBox(
            self,
            values=["PI", "Zweipunkt"],
            variable=self.regler_typ,
            command=self.update_visibility
        )
        self.regler_auswahl.pack(pady=(0, 10), padx=10, fill="x")

        self.kp_label = customtkinter.CTkLabel(self, text="K_p")
        self.kp_label.pack(pady=(5, 0), padx=10, anchor="w")
        self.kp_entry = customtkinter.CTkEntry(self, textvariable=self.k_p)
        self.kp_entry.pack(padx=10, fill="x")

        self.ki_label = customtkinter.CTkLabel(self, text="K_i")
        self.ki_label.pack(pady=(5, 0), padx=10, anchor="w")
        self.ki_entry = customtkinter.CTkEntry(self, textvariable=self.k_i)
        self.ki_entry.pack(padx=10, fill="x")

        self.toleranz_label = customtkinter.CTkLabel(self, text="Toleranz (°C)")
        self.toleranz_entry = customtkinter.CTkEntry(self, textvariable=self.toleranz)

        self.update_visibility(self.regler_typ.get())

    def update_visibility(self, value):
        if value == "PI":
            self.kp_label.pack(pady=(5, 0), padx=10, anchor="w")
            self.kp_entry.pack(padx=10, fill="x")
            self.ki_label.pack(pady=(5, 0), padx=10, anchor="w")
            self.ki_entry.pack(padx=10, fill="x")
            self.toleranz_label.pack_forget()
            self.toleranz_entry.pack_forget()
        elif value == "Zweipunkt":
            self.kp_label.pack_forget()
            self.kp_entry.pack_forget()
            self.ki_label.pack_forget()
            self.ki_entry.pack_forget()
            self.toleranz_label.pack(pady=(5, 0), padx=10, anchor="w")
            self.toleranz_entry.pack(padx=10, fill="x")

    def get_values(self):
        return {
            "typ": self.regler_typ.get(),
            "k_p": self.k_p.get(),
            "k_i": self.k_i.get(),
            "toleranz": self.toleranz.get()
        }


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Temperatur Simulation")
        #self.state('zoomed')
        
        #screen_width = self.winfo_screenwidth()
        #screen_height = self.winfo_screenheight()
        #self.geometry(f"{screen_width}x{screen_height}")

        self.update_idletasks()  # Fenster vorbereiten
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.after(0, lambda: self.state('zoomed'))

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.selected_csv_path = None
        self.selected_tsoll_path = None

        self.init_steuerung_panel()
        self.init_tabs()

    def init_steuerung_panel(self):
        #self.left_frame = customtkinter.CTkFrame(self)
        #self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        #  App scrollbar machen
        scrollable_container = customtkinter.CTkScrollableFrame(self, width=320)
        scrollable_container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_frame = scrollable_container


        # Datei-Auswahl
        customtkinter.CTkLabel(self.left_frame, text="Außentemperatur CSV wählen").pack(pady=(5, 0), padx=10, anchor="w")
        customtkinter.CTkButton(self.left_frame, text="CSV wählen", command=self.load_csv_file).pack(pady=(0, 10), padx=10, fill="x")

        customtkinter.CTkLabel(self.left_frame, text="T_soll Verlauf CSV wählen").pack(pady=(5, 0), padx=10, anchor="w")
        customtkinter.CTkButton(self.left_frame, text="T_soll CSV wählen", command=self.load_tsoll_file).pack(pady=(0, 10), padx=10, fill="x")

        # Physikalische Parameter
        params = [
            ("alpha", "Wärmeübergangskoeffizient alpha [W/m²·K]", 0.54),
            ("o", "Oberfläche O [m²]", 250),
            ("c", "Wärmekapazität c [J/kg·K]", 1010),
            ("m", "Masse m [kg]", 136000),
            ("t_soll", "Fallback-Solltemperatur T_soll [°C]", 22)
        ]

        self.entries = {}
        for key, label, default in params:
            customtkinter.CTkLabel(self.left_frame, text=label).pack(pady=(5, 0), padx=10, anchor="w")
            entry = customtkinter.CTkEntry(self.left_frame)
            entry.insert(0, str(default))
            entry.pack(pady=(0, 5), padx=10, fill="x")
            self.entries[key] = entry

        # Reglerauswahl
        customtkinter.CTkLabel(self.left_frame, text="Reglertyp").pack(pady=(10, 0), padx=10, anchor="w")
        self.regler_wahl = customtkinter.CTkComboBox(self.left_frame, values=["PI-Regler", "Zweipunktregler"])
        self.regler_wahl.set("PI-Regler")
        self.regler_wahl.pack(pady=(0, 10), padx=10, fill="x")

        # Regler-Eingaben
        customtkinter.CTkLabel(self.left_frame, text="Regler K_p").pack(pady=(10, 0), padx=10, anchor="w")
        self.k_p_entry = customtkinter.CTkEntry(self.left_frame)
        self.k_p_entry.insert(0, "2.7")
        self.k_p_entry.pack(padx=10, fill="x")

        customtkinter.CTkLabel(self.left_frame, text="Regler K_i").pack(pady=(10, 0), padx=10, anchor="w")
        self.k_i_entry = customtkinter.CTkEntry(self.left_frame)
        self.k_i_entry.insert(0, "3")
        self.k_i_entry.pack(padx=10, fill="x")

        # Toleranzfeld für Zweipunktregler
        customtkinter.CTkLabel(self.left_frame, text="Toleranz (°C) für Zweipunktregler").pack(pady=(10, 0), padx=10, anchor="w")
        self.hysterese_entry = customtkinter.CTkEntry(self.left_frame)
        self.hysterese_entry.insert(0, "0.5")
        self.hysterese_entry.pack(padx=10, fill="x")

        # Heizsystem Auswahl
        customtkinter.CTkLabel(self.left_frame, text="Heizsystem").pack(pady=(10, 0), padx=10, anchor="w")
        self.heizsystem = customtkinter.CTkComboBox(self.left_frame,
                                                    values=["Luftwärmepumpe", "Erdwärmepumpe (COP=5)", "Elektroheizung (COP=1)"])
        self.heizsystem.set("Luftwärmepumpe")
        self.heizsystem.pack(pady=(0, 10), padx=10, fill="x")

        # Buttons
        customtkinter.CTkButton(self.left_frame, text="Update Plot", command=self.update_plot).pack(pady=10, padx=10, fill="x")
        customtkinter.CTkButton(self.left_frame, text="Plot & Daten speichern", command=self.save_output).pack(pady=5, padx=10, fill="x")
        customtkinter.CTkButton(self.left_frame, text="Standard-Heizplan erzeugen", command=self.generate_tsoll_csv).pack(pady=5, padx=10, fill="x")
            
    def load_csv_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv")])
        if file_path:
            self.selected_csv_path = file_path
            tkinter.messagebox.showinfo("Datei gewählt", f"CSV-Datei geladen:\n{file_path}")

    def load_tsoll_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv")])
        if file_path:
            self.selected_tsoll_path = file_path
            tkinter.messagebox.showinfo("Datei gewählt", f"T_soll-Datei geladen:\n{file_path}")

    def extract_temp_from_csv(self, path):
        df = pd.read_csv(path, sep=";", header=None, names=["Zeit", "Temperatur"])
        df["Zeit"] = pd.to_datetime(df["Zeit"], format="%d.%m.%Y %H:%M")
        df = df.sort_values("Zeit").reset_index(drop=True)
        return df["Temperatur"].tolist(), df["Zeit"].tolist()

    def init_tabs(self):
        self.right_frame = customtkinter.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.tab_view = customtkinter.CTkTabview(self.right_frame)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.diagramm_tab = self.tab_view.add("Diagramm")
        self.init_diagramm_tab()

    def init_diagramm_tab(self):
        container = customtkinter.CTkFrame(self.diagramm_tab)
        container.grid(row=0, column=0, sticky="nsew")
        self.diagramm_tab.grid_rowconfigure(0, weight=1)
        self.diagramm_tab.grid_columnconfigure(0, weight=1)

        self.plot_area = customtkinter.CTkFrame(container)
        self.plot_area.grid(row=0, column=0, sticky="nsew")
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.controls_frame = customtkinter.CTkFrame(container, width=150)
        self.controls_frame.grid(row=0, column=1, sticky="ns", padx=10)

        self.show_temperature = tkinter.BooleanVar(value=True)
        self.show_outside = tkinter.BooleanVar(value=True)
        self.show_power = tkinter.BooleanVar(value=True)
        self.show_cop = tkinter.BooleanVar(value=True)
        self.show_energy = tkinter.BooleanVar(value=True)

        customtkinter.CTkLabel(self.controls_frame, text="Anzeigen:").pack(pady=10)
        for var, text in [
            (self.show_temperature, "Raumtemperatur"),
            (self.show_outside, "Außentemperatur"),
            (self.show_power, "P_el"),
            (self.show_cop, "COP"),
            (self.show_energy, "Energie [kWh]")
        ]:
            customtkinter.CTkCheckBox(self.controls_frame, text=text, variable=var).pack(anchor="w", padx=10)

        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar = NoCoordinatesToolbar(self.canvas, self.plot_area)
        self.toolbar.update()
        self.toolbar.pack(side="bottom", fill="x")
        reset_button = customtkinter.CTkButton(self.plot_area, text="Zoom zurücksetzen", command=self.reset_zoom)
        reset_button.pack(side="bottom", pady=5)

    def reset_zoom(self):
        if hasattr(self, "last_plot_data"):
            self.ax.set_xlim(self.last_plot_data["zeit"][0], self.last_plot_data["zeit"][-1])
            self.canvas.draw_idle()



    def save_output(self):
        if not hasattr(self, "last_plot_data"):
            tkinter.messagebox.showwarning("Keine Daten", "Bitte zuerst einen Plot erzeugen.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Dateien", "*.csv")])
        if not save_path:
            return

        df = pd.DataFrame({
            "Zeit": self.last_plot_data["zeit"],
            "Raumtemperatur [°C]": self.last_plot_data["T"],
            "Außentemperatur [°C]": self.last_plot_data["T_umg"],
            "T_soll [°C]": self.last_plot_data["T_soll"],
            "P_el [kW]": self.last_plot_data["P_el"],
            "COP": self.last_plot_data["cop"],
            "Energie [kWh]": self.last_plot_data["energie"]
        })
        df.to_csv(save_path, index=False, sep=";")
        self.fig.savefig(save_path.replace(".csv", ".png"))
        tkinter.messagebox.showinfo("Gespeichert", f"Daten & Plot gespeichert:\n{save_path}")

    def update_plot(self):
        params = self.get_parameters()
        if not params or not self.selected_csv_path:
            return

        try:
            df_umg = pd.read_csv(self.selected_csv_path, sep=";", header=None, names=["Zeit", "Temperatur"])
            df_umg["Zeit"] = pd.to_datetime(df_umg["Zeit"], format="%d.%m.%Y %H:%M")
            df_umg.sort_values("Zeit", inplace=True)
            T_umgebung_verlauf = df_umg["Temperatur"].tolist()
            zeitstempel = df_umg["Zeit"].tolist()
            n = len(T_umgebung_verlauf)

            if self.selected_tsoll_path:
                df_soll = pd.read_csv(self.selected_tsoll_path, sep=";", header=None, names=["Zeit", "Temperatur"])
                df_soll["Zeit"] = pd.to_datetime(df_soll["Zeit"], format="%d.%m.%Y %H:%M")
                df_soll.sort_values("Zeit", inplace=True)
                if not df_soll["Zeit"].equals(df_umg["Zeit"]):
                    raise ValueError("T_soll und Außentemperatur-Zeitstempel passen nicht.")
                T_soll_verlauf = df_soll["Temperatur"].tolist()
            else:
                T_soll_verlauf = [params["t_soll"]] * n
        except Exception as e:
            tkinter.messagebox.showerror("Fehler", str(e))
            return

        T = params["t_soll"]
        P_el_list, cop_list, temperaturen, energie_kum = [], [], [], []
        stromverbrauch_kWh, integral_error = 0, 0

        heizsystem = self.heizsystem.get()
        a, b = (0.1, 1) if heizsystem == "Luftwärmepumpe" else (0, 1)
        cop_constant = 5 if "Erdwärme" in heizsystem else 1

        # Reglerauswahl
        regeltyp = self.regler_wahl.get()

        if regeltyp == "PI-Regler":
            try:
                k_p = float(self.k_p_entry.get())
                k_i = float(self.k_i_entry.get())
            except ValueError:
                tkinter.messagebox.showerror("Fehler", "Ungültiger Wert für K_p oder K_i")
                return
        else:
            try:
                hysterese = float(self.hysterese_entry.get())
            except ValueError:
                tkinter.messagebox.showerror("Fehler", "Ungültiger Wert für Toleranz (Hysterese)")
                return

        for i in range(n):
            T_umg = T_umgebung_verlauf[i]
            T_soll = T_soll_verlauf[i]

            if regeltyp == "PI-Regler":
                delta_T = T_soll - T
                integral_error += delta_T / 60
                P_th = max(k_p * delta_T * 1_000_000 + k_i * integral_error * 1_000_000, 0)
            else:
                if T < T_soll - hysterese:
                    P_th = 10_000  # voller Betrieb
                elif T > T_soll + hysterese:
                    P_th = 0
                else:
                    P_th = 0

            cop = max(a * T_umg + b, cop_constant)
            P_el = min(P_th / cop, 10_000)
            P_v_dyn = P_el * cop
            stromverbrauch_kWh += P_el / 1000 / 60
            dT_dt = (P_v_dyn - params['alpha'] * params['o'] * (T - T_umg)) / (params['c'] * params['m'])
            T += dT_dt * 60
            temperaturen.append(T)
            P_el_list.append(P_el / 1000)
            cop_list.append(cop)
            energie_kum.append(stromverbrauch_kWh)

        # Plot
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        ax2 = self.ax.twinx()
        ax3 = self.ax.twinx()
        ax3.spines.right.set_position(("axes", 1.1))
        x_axis = zeitstempel
        lines, labels = [], []

        if self.show_temperature.get():
            l, = self.ax.plot(x_axis, temperaturen, label="Raumtemperatur [°C]")
            lines.append(l); labels.append(l.get_label())
        if self.show_outside.get():
            l, = self.ax.plot(x_axis, T_umgebung_verlauf, label="Außentemperatur [°C]", alpha=0.6)
            lines.append(l); labels.append(l.get_label())
        l, = self.ax.plot(x_axis, T_soll_verlauf, label="T_soll Verlauf [°C]", linestyle="--", color="gray")
        lines.append(l); labels.append(l.get_label())
        if self.show_power.get():
            l, = ax2.plot(x_axis, P_el_list, label="P_el [kW]", color="tab:red")
            lines.append(l); labels.append(l.get_label())
        if self.show_cop.get():
            l, = ax2.plot(x_axis, cop_list, label="COP", color="tab:green", linestyle="--")
            lines.append(l); labels.append(l.get_label())
        if self.show_energy.get():
            l, = ax3.plot(x_axis, energie_kum, label="Energie [kWh]", color="tab:purple", linestyle=":")
            lines.append(l); labels.append(l.get_label())

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m\n%H:%M'))
        self.ax.set_xlim(x_axis[0], x_axis[-1])
        self.ax.set_xlabel("Zeit")
        self.ax.set_ylabel("Temperatur (°C)")
        ax2.set_ylabel("P_el / COP", labelpad=15)
        ax3.set_ylabel("Energie (kWh)", labelpad=20)
        self.ax.set_title(f"Heizsystem: {heizsystem} | Verbrauch: {stromverbrauch_kWh:.2f} kWh")
        self.ax.grid(True)
        self.ax.legend(lines, labels, loc="upper left")
        self.fig.tight_layout()
        self.canvas.draw()

        self.last_plot_data = {
            "zeit": x_axis,
            "T": temperaturen,
            "T_umg": T_umgebung_verlauf,
            "T_soll": T_soll_verlauf,
            "P_el": P_el_list,
            "cop": cop_list,
            "energie": energie_kum
        }

    def generate_tsoll_csv(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Dateien", "*.csv")])
        if not save_path:
            return

        if self.selected_csv_path:
            df = pd.read_csv(self.selected_csv_path, sep=";", header=None, names=["Zeit", "Temperatur"])
            df["Zeit"] = pd.to_datetime(df["Zeit"], format="%d.%m.%Y %H:%M")
            zeiten = df["Zeit"].tolist()
        else:
            start_time = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            zeiten = [start_time + timedelta(minutes=i) for i in range(1440)]

        values = [22.0 if 6 <= t.hour < 22 else 21.5 for t in zeiten]
        df_out = pd.DataFrame({
            "Zeit": [t.strftime("%d.%m.%Y %H:%M") for t in zeiten],
            "Temperatur": values
        })
        df_out.to_csv(save_path, sep=";", index=False)
        tkinter.messagebox.showinfo("Erstellt", f"Heizplan gespeichert:\n{save_path}")

    def get_parameters(self):
        try:
            return {name: float(entry.get()) for name, entry in self.entries.items()}
        except ValueError:
            tkinter.messagebox.showerror("Fehler", "Ungültige Eingabewerte")
            return None

    def on_close(self):
        plt.close(self.fig)
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()