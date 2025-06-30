# Temperatur Simulation mit Heizkurve

Diese Anwendung simuliert den Raumtemperaturverlauf eines fiktiven Hauses mit Heizkurve und Außentemperatur.  
Die App basiert auf Python und ist mit jeder Python IDE ausführbar

## Ausführbare .exe Dateien

Ausführbare .exe Dateien für Windows Systeme wurden erstellt und sind unter /dist verfügbar

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