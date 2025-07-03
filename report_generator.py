def generate_report(data: dict) -> str:
    """Return formatted medical report."""
    lines = [
        f"🗂 Název dokumentu: {data['diagnosis']} – MKN-10: {data['mkn']} – Lékařská zpráva",
        f"🏷️ Tagy: {' '.join(f'#{t}' for t in data['tags'])}",
        f"💰 Cena za výkon: {data['price']} Kč",
        "",
        "**ZÁZNAM DO DOKUMENTACE**",
        "",
        "**Anamnéza**:",
    ]

    for key, text in data.get('anamnesis', {}).items():
        lines.append(f"{key}: {text or '...'}")

    lines.append("")
    lines.append("**Status praesens**:")
    for key, text in data.get('status', {}).items():
        lines.append(f"{key}: {text or '...'}")

    vitals = data.get('vitals')
    if vitals:
        lines.append("")
        lines.append("__Vitální funkce__:")
        for key, val in vitals.get('values', {}).items():
            lines.append(f"{key}: {val}")
        desc = vitals.get('desc')
        if desc:
            lines.append(desc)

    lines.append("")
    lines.append(f"**Vyšetření**: {data.get('examination') or '...'}")
    lines.append(f"**Terapie**: {data.get('therapy') or '...'}")

    lines.extend([
        "",
        "**Zapsal**:",
        "MUDr. asistent – Fero Lakatos",
        "Doctor-11 | Odznak: 97-5799",
    ])
    return "\n".join(lines)
