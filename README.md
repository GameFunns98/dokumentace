# Dokumentace

Tento repozitář obsahuje jednoduchý GUI nástroj **Generátor lékařské zprávy - Doctor-11** postavený na knihovně PySide6. Aplikace umožňuje vyplnit základní sekce lékařské zprávy, dopočítá celkovou cenu a po stisknutí tlačítka **Generovat zprávu** se vytvořený text automaticky zkopíruje do schránky.

Po spuštění aplikace je možné přepnout vzhled pomocí zaškrtávacího políčka **Tmavý režim**. Tato volba okamžitě aplikuje tmavé barevné schéma na celou aplikaci.

Krátká ukázka výsledného formátu zprávy:

```
OA: subjekt udává obtíže
PA: pacient popírá alergie

MUDr. asistent – Fero Lakatos, Doctor-11 | Odznak: 97-5799
```

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
