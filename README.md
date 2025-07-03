# Dokumentace

Tento repozitář obsahuje GUI nástroj **Generátor lékařské zprávy – Doctor‑11** postavený na knihovně PySide6. Formulář je rozdělen do několika skupin (anamnéza, status praesens, vyšetření, diagnóza a výstup). Aplikace automaticky dopočítá cenu zásahu podle zadaných parametrů a vygeneruje profesionální záznam připravený ke kopírování či uložení do TXT souboru.

Po spuštění lze vzhled přepnout pomocí políčka **Tmavý režim**, které okamžitě změní barevné schéma.

Krátká ukázka výsledného formátu zprávy:

```
🗂 Název dokumentu: Distorze kotníku – MKN-10: S93 – Lékařská zpráva
🏷️ Tagy: #s93 #distorzekotniku #mesto

💰 Cena za výkon: 2500 Kč

**ZÁZNAM DO DOKUMENTACE**

**Anamnéza**:
OA: ...
PA: ...

**Vyšetření**: ...
**Terapie**: ...

**Zapsal**:
MUDr. asistent – Fero Lakatos
Doctor-11 | Odznak: 97-5799
```

Cena lehkého ošetření lze zvolit ve spinneru (1000–1500 Kč), těžší ošetření je možné přičíst jedním kliknutím.

## Požadavky
- Python 3.10+
 - PySide6
 - requests

## Spuštění
```bash
pip install -r requirements.txt
python doctor11_gui.py
```
