# Dokumentace

Tento repozitář obsahuje jednoduchý GUI nástroj **Generátor lékařské zprávy - Doctor-11** postavený na knihovně PySide6. Aplikace umožňuje vyplnit základní sekce lékařské zprávy, dopočítá celkovou cenu a výsledek uloží do schránky.
Nově lze zprávu uložit do souboru `.txt` nebo `.pdf` a cena se počítá podle detailnějšího ceníku.
Generovaný text je navíc automaticky kopírován do schránky pro rychlé použití.

## Požadavky
- Python 3.10+
- PySide6

## Spuštění
```bash
pip install -r requirements.txt
python doctor11_gui.py
```
