# Praxis Projekt Energiemanagement

Im Rahmen eines Praxisprojektes zum Thema Energiemanagement erstellten wir ein Python Script um den Temperaturverlauf eines Hauses zu simulieren.
Ziel war es zu eruieren ob überhaupt Potential vorhanden ist um über ein Energiemanagement-System signifikant Energie zu sparen.
Die Projektdokumentation ist als PDF-Datei [(MEWI_Master_Projekt_EMS.pdf)](https://github.com/ingmaniac/Projekt-Energie-Management/blob/main/MEWI_Master_Projekt_EMS.pdf) dem Repository angefügt.

# Temperatur Simulation mit Heizkurve

Diese Anwendung simuliert den Raumtemperaturverlauf eines fiktiven Hauses mit Heizkurve und Außentemperatur.  
Die App basiert auf Python und ist mit jeder Python IDE ausführbar.
Eine Video Anleitung für die IDE Thonny finden sie unter folgendem Link
[-> Videoanleitung Thonny](https://youtu.be/CciGaAZ3K3E)

## Ausführbare .exe Dateien

Für Windows Nutzer ist eine ausführbare EXE Datei [Sim_Haus.exe](https://github.com/ingmaniac/Projekt-Energie-Management/blob/main/dist/Sim_Haus/Sim_Haus.exe) unter /Dist/Sim_Haus verfügbar.

## Bedienung der Grafischen Benutzeroberfläche

Übersicht über die GUI:

1. Parameter Menü
2. Diagrammfenster
3. Tabs Reiter
4. Diagramm Einträge aus-/einblenden
5. Diagramm Navigation

![Programmoberfläche](/assets/Anleitung/Programm.jpg)

1. Parameter Menü:
    - Monats-Tabs anzeigen: Ist diese Checkbox aktiv, wird die Diagramm Anzeige in Tabs je Monat unterteilt. In der Jahresübersicht werden alle Daten gesammelt angezeigt.
    - Aussentemperatur: hier werden die Eingabedaten aus einer CSV Datei geladen
    - T_Soll Verlauf: Soll Temperatur als CSV Datei laden
    - PV Einstrahlungsdaten: Hier können Einstrahlungsdaten als CSV Datei geladen werden. Wird keine CSV Datei geladen werden die folgenden Werte verwendet.
    - PV-Modulleistung: Nennleistung je Modul
    - Anzahl PV-Module: Gesamtanzahl der PV-Module
    - Wärmeübergangskoeffizient alpha: Wärmeübergangskoeffizient der Simulation
    - Oberfläche O: Oberfläche des gesamten Wärmeüberganges
    - Wärmekapazität: Wärmekapazität des zu simulierenden Hauses
    - Masse m: Masse der speicherfähigen Materialien
    - Fallback Solltemperatur T_Soll: Solltemperatur wenn kein T-Soll Verlauf geladen wurde.
    - Heizsystem: Luftwärmepumpe, Erdwärmepumpe oder Elektroheizung
    - Diagrammgröße: klein für kleine Bildschirme wie Laptops oder Anzeige mit Skalierung, mittel für normale Monitore und 1080p, groß für 4k
    - Update Plot: den Plot mit den gewählten Daten neu zeichnen
    - Plot & Daten speichern: experimentell
    - Standard-Heizplan erzeugen: experimentell

2. Diagramm Fenster:
    Hier werden die Diagramme gezeichnet

3. Tabs Reiter:
    Hier wird entweder die Diagrammüberschrift bzw. die Diagramm Tabs angezeigt (12 Monate  und die Jahresansicht)

4. Diagramm Einträge aus-/einblenden: 
    Hier kann mit den Checkboxen gewählt werden welche Daten angezeigt werden sollen

5. Diagramm Navigation:
    - ![Home](/assets/Anleitung/Home.png) Anzeige zurücksetzen
    - ![Zurück](/assets/Anleitung/Zurück.png) Zurück
    - ![Vor](/assets/Anleitung/Vor.png) Vor
    - ![Pan/Zoom](/assets/Anleitung/Pan.png) Pan / Zoom: linke Maustaste gedrückt halten zum Pan, rechte Maustaste gedrückt halten zum Zoomen
    - ![Zoom](/assets/Anleitung/Lukiluki.png) Rechteckiger Zoom: Zoom auf Rechteckauswahl mit der Maus
    - ![Einstellungen](/assets/Anleitung/Schiebedings.png) Plot Einstellungen mittels Schieberegler
    - ![Speichern](/assets/Anleitung/Diskette.png) Diagramm speichern

Eine Videoanleitung zur Bedienung ist unter folgendem Link erreichbar
[-> Videoanleitung GUI Sim_Haus.py](https://youtu.be/Wh7M2QwnfSA)

## 30.06.2025

Sim-Haus ersetzt alle vorigen Versionen, diese wurden nach /Archive verschoben
- Wahlweise kann eine Ansicht mit 13 Tabs für die einzelnen Monate und eine Jahresübersicht gewählt werden
- Aussentemperaturverlauf, Solltemperaturverlauf und PV Einstrahlungsdaten können per CSV eingelesen werden
- Die Diagrammgröße kann in 3 Stufen varriiert werden

## 26.05.2025

Heizung_PI_BetrOpt.py ersetzt vorherige Varianten
- automatisierte Reglerausgabe mit Betragsoptimum
- entfernt: alle unnötigen Schaltflächen
- erstellt: Testdatei mit Sprungantwort für Führungs und STörbetragsfunktion
- Verifikation der Testdatei
- Verkleinern des Diagramms (Zeile 245 ...figsize=(12, 7))
- Starten der Anwendung im Vollbild modus (Zeile 123 auskommentiert, Zeile 125 - 128 eingefügt)
- linkes Menü scollbar gemacht (Zeile 142 + 143 auskommentiert, Zeile 145 - 149 eingefügt)