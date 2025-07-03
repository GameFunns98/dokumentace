import sys
from PySide6 import QtWidgets, QtGui

SECTIONS = ["OA", "RA", "PA", "SA", "FA", "AA", "EA", "NO", "VF", "Subj.", "Obj.", "Vyšetření", "Terapie"]

LOCALITY_PRICES = {
    "Nemocnice": 0,
    "Město": 50,
    "Mimo město": 100,
    "Těžko přístupný terén": 200,
}

HEAVY_TREATMENT_EXTRA = 150
BASE_PRICE = 500

class ReportGenerator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generátor lékařské zprávy - Doctor-11")
        self.fields = {}
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
        layout.addLayout(form)
        self.result_box = QtWidgets.QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)
        self.price_label = QtWidgets.QLabel("Cena: 0 Kč")
        layout.addWidget(self.price_label)
        button = QtWidgets.QPushButton("Generovat zprávu")
        button.clicked.connect(self.generate_report)
        layout.addWidget(button)

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

    def generate_report(self):
        parts = []
        for section in SECTIONS:
            content = self.fields[section].toPlainText().strip()
            if content:
                parts.append(f"{section}: {content}")
        diag = self.diagnosis_edit.text().strip()
        if diag:
            parts.append(f"Diagnóza: {diag}")
        mkn = self.mkn_edit.text().strip()
        if mkn:
            parts.append(f"MKN-10: {mkn}")
        report = "\n".join(parts)
        report += "\n\n" + "MUDr. asistent – Fero Lakatos, Doctor-11 | Odznak: 97-5799"
        self.result_box.setPlainText(report)
        QtGui.QGuiApplication.clipboard().setText(report)
        price = BASE_PRICE + LOCALITY_PRICES[self.locality_combo.currentText()]
        if self.heavy_check.isChecked():
            price += HEAVY_TREATMENT_EXTRA
        self.price_label.setText(f"Cena: {price} Kč")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ReportGenerator()
    window.resize(600, 800)
    window.show()
    sys.exit(app.exec())
