import sys
import requests
from PySide6 import QtWidgets, QtGui, QtCore

# Individual sections grouped for the form layout
ANAM_SECTIONS = ["OA", "RA", "PA", "SA", "FA", "AA", "EA", "NO"]
STATUS_SECTIONS = ["VF", "Subj.", "Obj."]
EXAM_SECTIONS = ["Vyšetření", "Terapie"]

# Pricing constants according to EMS pricelist
LOCALITY_PRICES = {
    "Nemocnice": 1000,
    "Město": 1500,
    "Mimo město": 2000,
    "Těžko přístupný terén": 4000,
}

HEAVY_TREATMENT_EXTRA = 2000
# Default price for light treatment. The recommended range is
# 1000–1500 Kč. A spin box in the UI allows choosing a value
# within this range and falls back to this default if unchanged.
TREATMENT_LIGHT_MIN = 1000
TREATMENT_LIGHT_MAX = 1500
TREATMENT_LIGHT = 1250

MKN10_CACHE = None


def fetch_mkn10_online(code: str) -> str | None:
    """Return diagnosis description for the given MKN-10 code.

    Data are fetched from an online repository on first use and cached
    for subsequent lookups.
    """
    global MKN10_CACHE
    url = (
        "https://raw.githubusercontent.com/WhiteCoatAcademy/icd10/"
        "master/code-parsing/diagnosis_children.json"
    )
    try:
        if MKN10_CACHE is None:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            MKN10_CACHE = response.json()
        return MKN10_CACHE.get(code.upper(), {}).get("d")
    except Exception as exc:  # noqa: BLE001
        print(f"Could not fetch MKN-10 description: {exc}")
        return None

class ReportGenerator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generátor lékařské zprávy - Doctor-11")
        self.fields = {}
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # -------------------- Anamnesis --------------------
        anam_box = QtWidgets.QGroupBox("Anamnéza")
        anam_form = QtWidgets.QFormLayout()
        for section in ANAM_SECTIONS:
            text = QtWidgets.QTextEdit()
            self.fields[section] = text
            anam_form.addRow(section + ":", text)
        anam_box.setLayout(anam_form)
        layout.addWidget(anam_box)

        # -------------------- Status praesens --------------------
        status_box = QtWidgets.QGroupBox("Status praesens")
        status_form = QtWidgets.QFormLayout()
        for section in STATUS_SECTIONS:
            text = QtWidgets.QTextEdit()
            self.fields[section] = text
            status_form.addRow(section + ":", text)
        status_box.setLayout(status_form)
        layout.addWidget(status_box)

        # -------------------- Examination & Therapy --------------------
        exam_box = QtWidgets.QGroupBox("Vyšetření & Terapie")
        exam_form = QtWidgets.QFormLayout()
        for section in EXAM_SECTIONS:
            text = QtWidgets.QTextEdit()
            self.fields[section] = text
            exam_form.addRow(section + ":", text)
        exam_box.setLayout(exam_form)
        layout.addWidget(exam_box)

        # -------------------- Diagnosis and locality --------------------
        diag_box = QtWidgets.QGroupBox("Diagnóza & Lokalita zásahu")
        diag_form = QtWidgets.QFormLayout()
        self.diagnosis_edit = QtWidgets.QLineEdit()
        diag_form.addRow("Diagnóza:", self.diagnosis_edit)
        self.mkn_edit = QtWidgets.QLineEdit()
        self.mkn_edit.editingFinished.connect(self.lookup_mkn10)
        diag_form.addRow("MKN-10:", self.mkn_edit)
        self.locality_combo = QtWidgets.QComboBox()
        self.locality_combo.addItems(list(LOCALITY_PRICES.keys()))
        self.locality_combo.currentIndexChanged.connect(self.update_price)
        diag_form.addRow("Lokalita:", self.locality_combo)
        self.treatment_spin = QtWidgets.QSpinBox()
        self.treatment_spin.setRange(TREATMENT_LIGHT_MIN, TREATMENT_LIGHT_MAX)
        self.treatment_spin.setValue(TREATMENT_LIGHT)
        self.treatment_spin.valueChanged.connect(self.update_price)
        diag_form.addRow("Cena lehkého ošetření:", self.treatment_spin)
        self.heavy_check = QtWidgets.QCheckBox("Těžší ošetření (včetně bezvědomí)")
        self.heavy_check.toggled.connect(self.update_price)
        diag_form.addRow(self.heavy_check)
        self.price_label = QtWidgets.QLabel("Cena: 0 Kč")
        diag_form.addRow("Celková cena:", self.price_label)
        diag_box.setLayout(diag_form)
        layout.addWidget(diag_box)

        # -------------------- Output & actions --------------------
        output_box = QtWidgets.QGroupBox("Výstup & Akce")
        output_layout = QtWidgets.QVBoxLayout()
        self.result_box = QtWidgets.QTextEdit()
        self.result_box.setReadOnly(True)
        output_layout.addWidget(self.result_box)

        buttons_layout = QtWidgets.QHBoxLayout()
        gen_button = QtWidgets.QPushButton("Generovat")
        gen_button.clicked.connect(self.generate_report)
        buttons_layout.addWidget(gen_button)
        copy_button = QtWidgets.QPushButton("Kopírovat")
        copy_button.clicked.connect(self.copy_report)
        buttons_layout.addWidget(copy_button)
        export_button = QtWidgets.QPushButton("Export do TXT")
        export_button.clicked.connect(self.export_report)
        buttons_layout.addWidget(export_button)
        self.theme_check = QtWidgets.QCheckBox("Tmavý režim")
        self.theme_check.toggled.connect(self.toggle_theme)
        buttons_layout.addWidget(self.theme_check)
        output_layout.addLayout(buttons_layout)
        output_box.setLayout(output_layout)
        layout.addWidget(output_box)

    def lookup_mkn10(self):
        code = self.mkn_edit.text().strip()
        if not code:
            return
        desc = fetch_mkn10_online(code)
        if desc:
            self.diagnosis_edit.setText(desc)
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "MKN-10",
                "Nepodařilo se získat popis diagnózy."
            )

    def toggle_theme(self, enabled):
        app = QtWidgets.QApplication.instance()
        palette = app.palette()
        if enabled:
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("white"))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(35, 35, 35))
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor("white"))
        else:
            palette = QtGui.QPalette()
        app.setPalette(palette)

    # -------------------- Utility helpers --------------------
    def update_price(self) -> int:
        """Calculate and display the total price."""
        price = (
            self.treatment_spin.value()
            + LOCALITY_PRICES[self.locality_combo.currentText()]
        )
        if self.heavy_check.isChecked():
            price += HEAVY_TREATMENT_EXTRA
        self.price_label.setText(f"Cena: {price} Kč")
        return price

    def copy_report(self) -> None:
        """Copy the generated report to clipboard."""
        QtGui.QGuiApplication.clipboard().setText(self.result_box.toPlainText())

    def export_report(self) -> None:
        """Save the report to a text file."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Uložit zprávu", filter="Text files (*.txt)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.result_box.toPlainText())

    def generate_tags(self, mkn: str, diagnosis: str, locality: str) -> list[str]:
        """Return list of lower-case tags without spaces."""
        return [
            mkn.lower(),
            diagnosis.replace(" ", "").lower(),
            locality.replace(" ", "").lower(),
        ]

    def generate_report(self):
        diag = self.diagnosis_edit.text().strip()
        mkn = self.mkn_edit.text().strip()
        locality = self.locality_combo.currentText()

        price = self.update_price()
        tags = " ".join(f"#{t}" for t in self.generate_tags(mkn, diag, locality))

        lines = [
            f"🗂 Název dokumentu: {diag} – MKN-10: {mkn} – Lékařská zpráva",
            f"🏷️ Tagy: {tags}",
            f"💰 Cena za výkon: {price} Kč",
            "",
            "**ZÁZNAM DO DOKUMENTACE**",
            "",
            "**Anamnéza**:",
        ]
        for section in ANAM_SECTIONS:
            text = self.fields[section].toPlainText().strip() or "..."
            lines.append(f"{section}: {text}")

        lines.append("")
        lines.append("**Status praesens**:")
        for section in STATUS_SECTIONS:
            text = self.fields[section].toPlainText().strip() or "..."
            lines.append(f"{section}: {text}")

        lines.append("")
        for section in EXAM_SECTIONS:
            text = self.fields[section].toPlainText().strip() or "..."
            lines.append(f"**{section}**: {text}")

        lines.extend([
            "",
            "**Zapsal**:",
            "MUDr. asistent – Fero Lakatos",
            "Doctor-11 | Odznak: 97-5799",
        ])

        report = "\n".join(lines)
        self.result_box.setPlainText(report)
        self.copy_report()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ReportGenerator()
    window.resize(600, 800)
    window.show()
    sys.exit(app.exec())
