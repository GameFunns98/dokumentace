# Dokumentace

Tento repozitář obsahuje jednoduchý GUI nástroj **Generátor lékařské zprávy - Doctor-11** postavený na knihovně PySide6. Aplikace umožňuje vyplnit základní sekce lékařské zprávy, dopočítá celkovou cenu a výsledek uloží do schránky.

Od verze 2 aplikace obsahuje spinner pro volbu ceny lehkého ošetření.
Hodnota lze nastavit v rozmezí 1000–1500 Kč, výchozí cena je 1250 Kč.

## Požadavky
- Python 3.10+
- PySide6

## Spuštění
```bash
pip install -r requirements.txt
python doctor11_gui.py
```
