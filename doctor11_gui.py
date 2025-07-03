import sys
from PySide6 import QtWidgets, QtGui
from PySide6.QtPrintSupport import QPrinter

ANAMNESIS_SECTIONS = ["OA", "RA", "PA", "SA", "FA", "AA", "EA", "NO"]
STATUS_SECTIONS = ["VF", "Subj.", "Obj."]
OTHER_SECTIONS = ["Vyšetření", "Terapie"]
SECTIONS = ANAMNESIS_SECTIONS + STATUS_SECTIONS + OTHER_SECTIONS

LOCALITY_PRICES = {
    "Nemocnice": 1000,
    "Město": 1500,
    "Mimo město": 2000,
    "Těžko přístupný terén": 4000,
}

TREATMENT_LIGHT = 1250
TREATMENT_HEAVY = 2000

DIAGNOSTIC_PRICES = {
    "RTG": 250,
    "CT": 500,
    "MRI": 750,
    "SONO": 150,
}

class ReportGenerator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generátor lékařské zprávy - Doctor-11")
        self.fields = {}
        self.diagnostic_checks = {}
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        for section in SECTIONS:
            text = QtWidgets.QTextEdit()
            self.fields[section] = text
            form.addRow(section + ":", text)
        self.diagnosis_edit = QtWidgets.QLineEdit()
        form.addRow("Diagnóza:", self.diagnosis_edit)
        self.mkn_edit = QtWidgets.QLineEdit()
        form.addRow("MKN-10:", self.mkn_edit)
        self.locality_combo = QtWidgets.QComboBox()
        self.locality_combo.addItems(list(LOCALITY_PRICES.keys()))
        form.addRow("Lokalita:", self.locality_combo)
        self.heavy_check = QtWidgets.QCheckBox("Těžší ošetření (včetně bezvědomí)")
        form.addRow(self.heavy_check)

        diag_layout = QtWidgets.QHBoxLayout()
        for name in DIAGNOSTIC_PRICES:
            chk = QtWidgets.QCheckBox(name)
            self.diagnostic_checks[name] = chk
            diag_layout.addWidget(chk)
        form.addRow("Diagnostika:", diag_layout)
        layout.addLayout(form)
        self.result_box = QtWidgets.QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)
        self.price_label = QtWidgets.QLabel("Cena: 0 $")
        layout.addWidget(self.price_label)
        btn_layout = QtWidgets.QHBoxLayout()
        gen_btn = QtWidgets.QPushButton("Generovat zprávu")
        gen_btn.clicked.connect(self.generate_report)
        btn_layout.addWidget(gen_btn)
        txt_btn = QtWidgets.QPushButton("Uložit TXT")
        txt_btn.clicked.connect(self.export_txt)
        btn_layout.addWidget(txt_btn)
        pdf_btn = QtWidgets.QPushButton("Uložit PDF")
        pdf_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(pdf_btn)
        layout.addLayout(btn_layout)

        self.theme_check = QtWidgets.QCheckBox("Tmavý režim")
        self.theme_check.toggled.connect(self.toggle_theme)
        layout.addWidget(self.theme_check)

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

    def export_txt(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Uložit TXT", filter="Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.result_box.toPlainText())

    def export_pdf(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Uložit PDF", filter="PDF Files (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            doc = QtGui.QTextDocument(self.result_box.toPlainText())
            doc.print(printer)

    def fetch_mkn10_online(self, code: str):
        """Budoucí integrace online databáze MKN-10."""
        # TODO: implement online lookup of MKN-10 codes
        return ""

    def generate_report(self):
        diag = self.diagnosis_edit.text().strip()
        mkn = self.mkn_edit.text().strip()

        title_parts = []
        if mkn:
            title_parts.append(mkn)
        if diag:
            title_parts.append(diag)
        title = "Lékařská zpráva" + (" - " + " ".join(title_parts) if title_parts else "")

        tags = []
        if mkn:
            tags.append(f"#{mkn}")
        if self.heavy_check.isChecked():
            tags.append("#bezvedomi")
        tags.append(f"#{self.locality_combo.currentText().replace(' ', '').lower()}")

        lines = [f"**{title}**"]
        if tags:
            lines.append(" ".join(tags))
        lines.append("")

        if any(self.fields[s].toPlainText().strip() for s in ANAMNESIS_SECTIONS):
            lines.append("__Anamnéza__:")
            for sec in ANAMNESIS_SECTIONS:
                content = self.fields[sec].toPlainText().strip()
                if content:
                    lines.append(f"* **{sec}:** {content}")
            lines.append("")

        if any(self.fields[s].toPlainText().strip() for s in STATUS_SECTIONS):
            lines.append("__Status praesens__:")
            for sec in STATUS_SECTIONS:
                content = self.fields[sec].toPlainText().strip()
                if content:
                    lines.append(f"* **{sec}:** {content}")
            lines.append("")

        vysetreni = self.fields["Vyšetření"].toPlainText().strip()
        if vysetreni:
            lines.append("__Vyšetření__:")
            lines.append(vysetreni)
            lines.append("")

        terapie = self.fields["Terapie"].toPlainText().strip()
        if terapie:
            lines.append("__Terapie__:")
            lines.append(terapie)
            lines.append("")

        lines.append("__Zapsal__:")
        lines.append("MUDr. asistent – Fero Lakatos")
        lines.append("Doctor-11 | Odznak: 97-5799")

        report = "\n".join(lines)
        self.result_box.setPlainText(report)
        QtGui.QGuiApplication.clipboard().setText(report)

        price = LOCALITY_PRICES[self.locality_combo.currentText()]
        price += TREATMENT_HEAVY if self.heavy_check.isChecked() else TREATMENT_LIGHT
        for name, chk in self.diagnostic_checks.items():
            if chk.isChecked():
                price += DIAGNOSTIC_PRICES[name]
        self.price_label.setText(f"Cena: {price} $")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ReportGenerator()
    window.resize(600, 800)
    window.show()
    sys.exit(app.exec())
