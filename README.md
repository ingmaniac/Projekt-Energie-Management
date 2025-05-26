# Temperatur Simulation mit Heizkurve

Diese Anwendung simuliert den Raumtemperaturverlauf über 24 Stunden mit Heizkurve und Außentemperatur.  
Die App basiert auf Python und ist mit jeder Python IDE ausführbar

## Ausführbare .exe Dateien

Ausführbare .exe Dateien für Windows Systeme wurden erstellt und sind unter /dist verfügbar

## 26.05.2025

Heizung_PI_BetrOpt.py ersetzt vorherige Varianten
- automatisierte Reglerausgabe mit Betragsoptimum
- entfernt: alle unnötigen Schaltflächen
- erstellt: Testdatei mit Sprungantwort für Führungs und STörbetragsfunktion
- Verifikation der Testdatei
- Verkleinern des Diagramms (Zeile 245 ...figsize=(12, 7))
- Starten der Anwendung im Vollbild modus (Zeile 123 auskommentiert, Zeile 125 - 128 eingefügt)
- linkes Menü scollbar gemacht (Zeile 142 + 143 auskommentiert, Zeile 145 - 149 eingefügt)