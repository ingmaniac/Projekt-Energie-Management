import matplotlib.pyplot as plt
import tkinter
import tkinter.messagebox
import customtkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import filedialog
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from pvlib import solarposition, irradiance

class NoCoordinatesToolbar(NavigationToolbar2Tk):
    def set_message(self, s):
        pass

    def zoom(self, *args):
        super().zoom(*args)
        for ax in self.canvas.figure.axes:
            ax._zoom_mode = 'x'

    def __init__(self, canvas, window):
        super().__init__(canvas, window)


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

        # Variable für die Anzeige von Monats-Tabs
        self.use_tabs = tkinter.BooleanVar(value=True)
        # Variable für die Plot-Größe
        self.plot_size_option = tkinter.StringVar(value="mittel")

        # Als Vollbild starten
        self.update_idletasks()  # Fenster vorbereiten
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.after(0, lambda: self.state('zoomed')) # Für Windows, um direkt im Vollbildmodus zu starten

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.selected_csv_path = None
        self.selected_tsoll_path = None

        self.init_steuerung_panel()
        self.init_tabs()
        


    def init_steuerung_panel(self):
        # Scrollbalken einfügen im Menü
        scrollable_container = customtkinter.CTkScrollableFrame(self, width=280)
        scrollable_container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_frame = scrollable_container
        # Ende Scrollbalken einfügen

        # Auswahl ob Monats-Tabs oder Jahresübersicht
        customtkinter.CTkLabel(self.left_frame, text="Ansicht").pack(pady=(10, 0), padx=10, anchor="w")
        customtkinter.CTkCheckBox(self.left_frame, text="Monats-Tabs anzeigen", variable=self.use_tabs, command=self.toggle_view).pack(padx=10, anchor="w")
        # Datei-Auswahl
        customtkinter.CTkLabel(self.left_frame, text="Eingabewerte aus CSV laden").pack(pady=(5, 0), padx=10, anchor="w")
        # gemeinsames Label spart Platz
        customtkinter.CTkButton(self.left_frame, text="Aussentemperatur", command=self.load_csv_file).pack(pady=(0, 10), padx=10, fill="x")
        customtkinter.CTkButton(self.left_frame, text="T_Soll Verlauf", command=self.load_tsoll_file).pack(pady=(0, 10), padx=10, fill="x")
        customtkinter.CTkButton(self.left_frame, text="PV Einstrahlungsdaten", command=self.load_pv_file).pack(pady=(0, 10), padx=10, fill="x")

        # Parameter
        params = [
            # PV Parameter
            ("pv_modulleistung", "PV-Modulleistung [kWp]", 0.3),
            ("pv_modulanzahl", "Anzahl PV-Module", 20),
            # physikalisch Parameter
            ("alpha", "Wärmeübergangskoeffizient alpha [W/m²·K]", 0.39),
            ("o", "Oberfläche O [m²]", 250),
            ("c", "Wärmekapazität c [J/kg·K]", 950),
            ("m", "Masse m [kg]", 160000),
            ("t_soll", "Fallback-Solltemperatur T_soll [°C]", 22)
        ]

        self.entries = {}
        for key, label, default in params:
            customtkinter.CTkLabel(self.left_frame, text=label).pack(pady=(5, 0), padx=10, anchor="w")
            entry = customtkinter.CTkEntry(self.left_frame)
            entry.insert(0, str(default))
            entry.pack(pady=(0, 4), padx=10, fill="x")
            self.entries[key] = entry

        # Heizsystem Auswahl
        customtkinter.CTkLabel(self.left_frame, text="Heizsystem").pack(pady=(5, 0), padx=10, anchor="w")
        self.heizsystem = customtkinter.CTkComboBox(self.left_frame,
                                                    values=["Luftwärmepumpe", "Erdwärmepumpe (COP=5)", "Elektroheizung (COP=1)"])
        self.heizsystem.set("Luftwärmepumpe")
        self.heizsystem.pack(pady=(0, 4), padx=10, fill="x")

        # Auswahl Diagrammgröße
        customtkinter.CTkLabel(self.left_frame, text="Diagrammgröße").pack(pady=(5, 0), padx=10, anchor="w")
        self.plot_size_menu = customtkinter.CTkComboBox(
            self.left_frame,
            values=["klein", "mittel", "groß"],
            variable=self.plot_size_option,
            state="readonly",
            command=self.apply_plot_size_change
        )
        self.plot_size_menu.pack(pady=(0, 10), padx=10, fill="x")


        # Buttons
        customtkinter.CTkButton(self.left_frame, text="Update Plot", command=self.update_plot).pack(pady=10, padx=10, fill="x")
        customtkinter.CTkButton(self.left_frame, text="Plot & Daten speichern", command=self.save_output).pack(pady=5, padx=10, fill="x")
        customtkinter.CTkButton(self.left_frame, text="Standard-Heizplan erzeugen", command=self.generate_tsoll_csv).pack(pady=5, padx=10, fill="x")
            
    def load_csv_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv")])
        if file_path:
            self.selected_csv_path = file_path

    def load_pv_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv")])
        if file_path:
            self.selected_pv_path = file_path

    def load_tsoll_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv")])
        if file_path:
            self.selected_tsoll_path = file_path

    def extract_temp_from_csv(self, path):
        df = pd.read_csv(path, sep=";", header=None, names=["Zeit", "Temperatur"])
        df["Zeit"] = pd.to_datetime(df["Zeit"], format="%d.%m.%Y %H:%M")
        df = df.sort_values("Zeit").reset_index(drop=True)
        return df["Temperatur"].tolist(), df["Zeit"].tolist()

    def apply_plot_size_change(self, _=None):
        self.toggle_view()
        self.update_plot()

    def toggle_view(self):
        # Plots schließen bevor neue erstellt werden
        if hasattr(self, "plot_tabs"):
            for plot in self.plot_tabs.values():
                plt.close(plot["fig"])
        if hasattr(self, "gesamt_plot"):
            plt.close(self.gesamt_plot["fig"])

        if hasattr(self, "tab_view"):
            self.tab_view.destroy()

        self.right_frame = customtkinter.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.controls_frame = customtkinter.CTkFrame(self.right_frame, width=150)
        self.controls_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

        # Kontrollkästchen (erneut anlegen)
        self.show_temperature = tkinter.BooleanVar(value=True)
        self.show_outside = tkinter.BooleanVar(value=True)
        self.show_tsoll = tkinter.BooleanVar(value=False)
        self.show_power = tkinter.BooleanVar(value=True)
        self.show_cop = tkinter.BooleanVar(value=True)
        self.show_energy = tkinter.BooleanVar(value=True)
        self.show_pv = tkinter.BooleanVar(value=True)

        customtkinter.CTkLabel(self.controls_frame, text="Anzeigen:").pack(pady=10)
        for var, text in [
            (self.show_temperature, "Raumtemperatur"),
            (self.show_outside, "Außentemperatur"),
            (self.show_tsoll, "Solltemperatur"),
            (self.show_power, "P_el"),
            (self.show_cop, "COP"),
            (self.show_energy, "Energie [kWh]"),
            (self.show_pv, "PV")
        ]:
            customtkinter.CTkCheckBox(self.controls_frame, text=text, variable=var).pack(anchor="w", padx=10)

        # Tabs oder Einzelansicht erstellen
        self.tab_view = customtkinter.CTkTabview(self.right_frame)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.plot_tabs = {}
        if self.use_tabs.get():
            for i, monat in enumerate([
                "Januar", "Februar", "März", "April", "Mai", "Juni",
                "Juli", "August", "September", "Oktober", "November", "Dezember"
            ], 1):
                tab = self.tab_view.add(monat)
                self.plot_tabs[i] = self.init_diagramm_tab(tab)
            self.gesamt_tab = self.tab_view.add("Jahresübersicht")
            self.gesamt_plot = self.init_diagramm_tab(self.gesamt_tab)
            self.tab_view.set("Jahresübersicht")  # Jahresübersicht standardmäßig aktiv
        else:
            tab = self.tab_view.add("Diagramm")
            self.gesamt_plot = self.init_diagramm_tab(tab)
        

    def init_tabs(self):
        self.toggle_view()

    def init_diagramm_tab(self, parent_tab):
        container = customtkinter.CTkFrame(parent_tab)
        container.grid(row=0, column=0, sticky="nsew")
        parent_tab.grid_rowconfigure(0, weight=1)
        parent_tab.grid_columnconfigure(0, weight=1)

        plot_area = customtkinter.CTkFrame(container)
        plot_area.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        
        # Diagrammgröße ändern
        size_map = {
            "klein": (8, 5),
            "mittel": (12, 7),
            "groß": (20, 12)
        }
        figsize = size_map.get(self.plot_size_option.get(), (12, 7))
        fig, ax = plt.subplots(figsize=figsize)

        canvas = FigureCanvasTkAgg(fig, master=plot_area)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NoCoordinatesToolbar(canvas, plot_area)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        return {
            "fig": fig,
            "ax": ax,
            "canvas": canvas,
            "controls_frame": self.controls_frame,
            "toolbar": toolbar,
            "plot_area": plot_area
        }

    
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

        if "PV" in self.last_plot_data:
            df["PV-Leistung [kW]"] = self.last_plot_data["PV"]

        df.to_csv(save_path, index=False, sep=";")
        self.gesamt_plot["fig"].savefig(save_path.replace(".csv", ".png"))
        tkinter.messagebox.showinfo("Gespeichert", f"Daten & Plot gespeichert:\n{save_path}")

    def calculate_magnitude_optimum(self, alpha, o, c, m):
        scaling_factor = 1000000000
        try:
            A = alpha * o
            if A <= 0:
                raise ValueError("Ungültige Werte für Alpha oder Fläche.")
            tau = (c * m) / A                      # Zeitkonstante in Zeitbasis
            K_s = 1 / A                            # statische Verstärkung der Strecke
            K_p = 1 / (K_s * tau)                  # Reglerverstärkung nach Betragsoptimum
            T_n = tau                              # Nachstellzeit = Zeitkonstante

            return {
                "K_p": scaling_factor*K_p, 
                "K_i": scaling_factor*K_p / T_n, 
                "T_n": T_n,
                "K_s": K_s,
                "tau": tau
            }
        except Exception as e:
            raise ValueError(f"Fehler bei Berechnung des Betragsoptimums: {e}")


    def calculate_pv_power(self,df, latitude=48.1667, longitude=14.0333,
                        tilt=30, azimuth=182, module_power_kwp=0.3,
                        num_modules=20, efficiency=0.18):

        total_kwp = module_power_kwp * num_modules
        surface_area = (total_kwp * 1000) / (efficiency * 1000)  # Fläche in m²

        solpos = solarposition.get_solarposition(df.index, latitude, longitude)
        dni = df["Wert"]
        dhi = dni * 0.2
        ghi = dni + dhi

        poa = irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            dni=dni,
            ghi=ghi,
            dhi=dhi,
            solar_zenith=solpos["zenith"],
            solar_azimuth=solpos["azimuth"]
        )

        df = df.copy()
        df["Leistung_W"] = poa["poa_global"] * surface_area * efficiency
        return df

    def update_plot(self):
        import calendar
        t_base = 600  # Zeitschritt in Sekunden (10 Minuten)

        # --- Zugriff auf Plot-Elemente der Jahresübersicht ---
        gesamt_plot = self.gesamt_plot
        fig = gesamt_plot["fig"]
        canvas = gesamt_plot["canvas"]

        fig.clf()
        ax = fig.add_subplot(111)
        ax2 = ax.twinx()
        ax3 = ax.twinx()
        ax3.spines.right.set_position(("axes", 1.1))

        params = self.get_parameters()
        if not params or not self.selected_csv_path:
            return

        try:
            df_umg = pd.read_csv(self.selected_csv_path, sep=";", header=None, names=["Zeit", "Temperatur"])
            df_umg["Zeit"] = pd.to_datetime(df_umg["Zeit"], format="%d.%m.%Y %H:%M")
            df_umg.sort_values("Zeit", inplace=True)
            T_umgebung_verlauf = df_umg["Temperatur"].tolist()
            zeitstempel = df_umg["Zeit"].tolist()
            x_axis = zeitstempel
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
            tkinter.messagebox.showerror("Fehler beim Einlesen der Daten", str(e))
            return

        T = params["t_soll"]
        P_el_list, cop_list, temperaturen, energie_kum = [], [], [], []
        stromverbrauch_kWh, integral_error = 0.0, 0.0

        heizsystem = self.heizsystem.get()
        a, b = (0.1, 1) if heizsystem == "Luftwärmepumpe" else (0, 1)
        cop_constant = 5 if "Erdwärme" in heizsystem else 1

        try:
            opt = self.calculate_magnitude_optimum(params["alpha"], params["o"], params["c"], params["m"])
            k_p = opt["K_p"]
            k_i = opt["K_i"]
        except Exception as e:
            tkinter.messagebox.showerror("Reglerfehler", str(e))
            return

        for i in range(n):
            T_umg = T_umgebung_verlauf[i]
            T_soll = T_soll_verlauf[i]

            delta_T = T_soll - T
            integral_error += delta_T * t_base
            P_th = max(min(k_p * delta_T + k_i * integral_error, 20000), 0)
            cop = max(a * T_umg + b, cop_constant)
            if cop <= 0 or not isinstance(cop, (int, float)):
                cop = 1
            P_el = max(min(P_th / cop, 10000), 0)
            stromverbrauch_kWh += P_el * t_base / 3600 / 1000

            dT_dt = (P_th - params['alpha'] * params['o'] * (T - T_umg)) / (params['c'] * params['m'])
            T += dT_dt * t_base

            temperaturen.append(T)
            P_el_list.append(P_el / 1000)
            cop_list.append(cop)
            energie_kum.append(stromverbrauch_kWh)

        df_pv_reindexed = None
        if hasattr(self, "selected_pv_path") and self.show_pv.get():
            try:
                df_pv_input = pd.read_csv(self.selected_pv_path, sep=";", header=None, names=["Datum", "Wert"])
                df_pv_input["Datum"] = pd.to_datetime(df_pv_input["Datum"], format="%d.%m.%Y %H:%M")
                df_pv_input.set_index("Datum", inplace=True)

                modulleistung_kwp = float(self.entries["pv_modulleistung"].get())
                anzahl_module = int(self.entries["pv_modulanzahl"].get())

                df_pv = self.calculate_pv_power(df_pv_input,
                                                module_power_kwp=modulleistung_kwp,
                                                num_modules=anzahl_module)
                df_pv_kW = df_pv["Leistung_W"] / 1000
                df_pv_reindexed = df_pv_kW.reindex(x_axis, method="nearest")
            except Exception as e:
                print("Fehler beim Einlesen der PV-Leistung:", e)

        # --- Daten speichern ---
        self.last_plot_data = {
            "zeit": x_axis,
            "T": temperaturen,
            "T_umg": T_umgebung_verlauf,
            "T_soll": T_soll_verlauf,
            "P_el": P_el_list,
            "cop": cop_list,
            "energie": energie_kum
        }
        if df_pv_reindexed is not None:
            self.last_plot_data["PV"] = df_pv_reindexed.tolist()

        # --- Plot: Jahresübersicht ---
        lines, labels = [], []
        if self.show_temperature.get():
            l, = ax.plot(x_axis, temperaturen, label="Raumtemperatur [°C]")
            lines.append(l); labels.append(l.get_label())
        if self.show_outside.get():
            l, = ax.plot(x_axis, T_umgebung_verlauf, label="Außentemperatur [°C]", alpha=0.6)
            lines.append(l); labels.append(l.get_label())
        if self.show_tsoll.get():
            l, = ax.plot(x_axis, T_soll_verlauf, label="T_soll Verlauf [°C]", linestyle="--", color="gray")
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
        if self.show_pv.get() and df_pv_reindexed is not None:
            l, = ax2.plot(x_axis, df_pv_reindexed, label="PV-Leistung [kW]", color="orange", linestyle="--")
            lines.append(l); labels.append(l.get_label())

        ax.set_title(f"Heizsystem: {heizsystem} | Verbrauch: {stromverbrauch_kWh:.2f} kWh")
        ax.set_xlabel("Zeit")
        ax.set_ylabel("Temperatur (°C)")
        ax2.set_ylabel("P_el (kW), COP")
        ax3.set_ylabel("Energie [kWh]", labelpad=20)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m\n%H:%M'))
        ax.set_xlim(x_axis[0], x_axis[-1])
        ax.grid(True)
        ax.legend(lines, labels, loc="upper left")
        fig.tight_layout()
        canvas.draw()

        # Monats-Tabs nur erzeugen, wenn Tabs-Modus aktiv
        if self.use_tabs.get():
            # --- Monats-Tabs aktualisieren ---
            df_plot = pd.DataFrame({
                "Zeit": x_axis,
                "Raumtemperatur": temperaturen,
                "Außentemperatur": T_umgebung_verlauf,
                "T_soll": T_soll_verlauf,
                "P_el": P_el_list,
                "COP": cop_list,
                "Energie": energie_kum,
                "PV": self.last_plot_data.get("PV", [None] * len(x_axis))
            })
            df_plot["Zeit"] = pd.to_datetime(df_plot["Zeit"])

            for monat in range(1, 13):
                tab_plot = self.plot_tabs[monat]
                fig = tab_plot["fig"]
                fig.clf()
                ax = fig.add_subplot(111)
                ax2 = ax.twinx()
                ax3 = ax.twinx()
                ax3.spines.right.set_position(("axes", 1.1))

                df_monat = df_plot[df_plot["Zeit"].dt.month == monat]
                if df_monat.empty:
                    continue

                lines, labels = [], []
                if self.show_temperature.get():
                    l, = ax.plot(df_monat["Zeit"], df_monat["Raumtemperatur"], label="Raumtemperatur [°C]")
                    lines.append(l); labels.append(l.get_label())
                if self.show_outside.get():
                    l, = ax.plot(df_monat["Zeit"], df_monat["Außentemperatur"], label="Außentemperatur [°C]")
                    lines.append(l); labels.append(l.get_label())
                if self.show_tsoll.get():
                    l, = ax.plot(df_monat["Zeit"], df_monat["T_soll"], label="T_soll [°C]", linestyle="--", color="gray")
                    lines.append(l); labels.append(l.get_label())
                if self.show_power.get():
                    l, = ax2.plot(df_monat["Zeit"], df_monat["P_el"], label="P_el [kW]", color="red")
                    lines.append(l); labels.append(l.get_label())
                if self.show_cop.get():
                    l, = ax2.plot(df_monat["Zeit"], df_monat["COP"], label="COP", color="green", linestyle="--")
                    lines.append(l); labels.append(l.get_label())
                if self.show_energy.get():
                    l, = ax3.plot(df_monat["Zeit"], df_monat["Energie"], label="Energie [kWh]", color="purple", linestyle=":")
                    lines.append(l); labels.append(l.get_label())
                if self.show_pv.get() and "PV" in df_monat.columns:
                    l, = ax2.plot(df_monat["Zeit"], df_monat["PV"], label="PV-Leistung [kW]", color="orange", linestyle="--")
                    lines.append(l); labels.append(l.get_label())

                ax.set_title(calendar.month_name[monat])
                ax.set_xlabel("Zeit")
                ax.set_ylabel("Temperatur / Leistung")
                ax2.set_ylabel("P_el / COP")
                ax3.set_ylabel("Energie [kWh]", labelpad=20)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m\n%H:%M'))
                ax.grid(True)
                ax.legend(lines, labels, loc="upper left")
                fig.tight_layout()
                tab_plot["canvas"].draw()


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
        # Alle Figuren schließen
        for plot in self.plot_tabs.values():
            plt.close(plot["fig"])
        plt.close(self.gesamt_plot["fig"])
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()