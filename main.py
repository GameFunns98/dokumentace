from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtWidgets, QtGui, QtCore

import mkn10
import pricing
import report_generator
import theme

ANAM_SECTIONS = ["OA", "RA", "PA", "SA", "FA", "AA", "EA", "NO"]
STATUS_SECTIONS = ["VF", "Subj.", "Obj."]
EXAM_SECTIONS = ["Vyšetření", "Terapie"]

DATA_PATH = Path(__file__).resolve().parent / "data" / "diagnosis_children.json"


class ReportGenerator(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        mkn10.load_mkn10_data(str(DATA_PATH))

        self.setWindowTitle("Generátor lékařské zprávy - Doctor-11")
        self.setMinimumSize(600, 700)
        self.fields: dict[str, QtWidgets.QTextEdit] = {}
        self.diagnostic_checks: dict[str, QtWidgets.QCheckBox] = {}
        self.init_ui()
        self.update_price()

    # -------------------- UI setup --------------------
    def init_ui(self) -> None:
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        container = QtWidgets.QWidget()
        scroll_area.setWidget(container)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # -------------------- Anamnesis --------------------
        anam_box = QtWidgets.QGroupBox("Anamnéza")
        anam_form = QtWidgets.QFormLayout()
        for section in ANAM_SECTIONS:
            text = QtWidgets.QTextEdit()
            text.setMinimumHeight(60)
            self.fields[section] = text
            anam_form.addRow(section + ":", text)
        anam_box.setLayout(anam_form)
        layout.addWidget(anam_box)

        # -------------------- Status praesens --------------------
        status_box = QtWidgets.QGroupBox("Status praesens")
        status_form = QtWidgets.QFormLayout()
        for section in STATUS_SECTIONS:
            text = QtWidgets.QTextEdit()
            text.setMinimumHeight(60)
            self.fields[section] = text
            status_form.addRow(section + ":", text)
        status_box.setLayout(status_form)
        layout.addWidget(status_box)

        # -------------------- Examination & Therapy --------------------
        exam_box = QtWidgets.QGroupBox("Vyšetření & Terapie")
        exam_form = QtWidgets.QFormLayout()
        for section in EXAM_SECTIONS:
            text = QtWidgets.QTextEdit()
            text.setMinimumHeight(60)
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
        completer = QtWidgets.QCompleter(mkn10.get_all_codes())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.mkn_edit.setCompleter(completer)
        completer.activated.connect(self.lookup_mkn10)
        diag_form.addRow("MKN-10:", self.mkn_edit)
        self.locality_combo = QtWidgets.QComboBox()
        self.locality_combo.addItems(list(pricing.LOCALITY_PRICES.keys()))
        self.locality_combo.currentIndexChanged.connect(self.update_price)
        diag_form.addRow("Lokalita:", self.locality_combo)
        self.treatment_spin = QtWidgets.QSpinBox()
        self.treatment_spin.setRange(1000, 1500)
        self.treatment_spin.setValue(1250)
        self.treatment_spin.valueChanged.connect(self.update_price)
        diag_form.addRow("Cena lehkého ošetření:", self.treatment_spin)
        self.heavy_check = QtWidgets.QCheckBox("Těžší ošetření (včetně bezvědomí)")
        self.heavy_check.toggled.connect(self.update_price)
        diag_form.addRow(self.heavy_check)

        diag_group = QtWidgets.QGroupBox("Diagnostika")
        diag_layout = QtWidgets.QHBoxLayout()
        for name in pricing.DIAGNOSTIC_PRICES:
            chk = QtWidgets.QCheckBox(name)
            chk.toggled.connect(self.update_price)
            self.diagnostic_checks[name] = chk
            diag_layout.addWidget(chk)
        diag_group.setLayout(diag_layout)
        diag_form.addRow(diag_group)

        self.price_label = QtWidgets.QLabel("Cena: 0 Kč")
        diag_form.addRow("Celková cena:", self.price_label)
        diag_box.setLayout(diag_form)
        layout.addWidget(diag_box)

        # -------------------- Output & actions --------------------
        output_box = QtWidgets.QGroupBox("Výstup & Akce")
        output_layout = QtWidgets.QVBoxLayout()
        self.result_box = QtWidgets.QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setMinimumHeight(60)
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

    # -------------------- Utility helpers --------------------
    def lookup_mkn10(self) -> None:
        code = self.mkn_edit.text().strip()
        if not code:
            return
        desc = mkn10.get_description(code)
        if desc:
            self.diagnosis_edit.setText(desc)
        else:
            QtWidgets.QMessageBox.warning(self, "MKN-10", "Nepodařilo se najít popis diagnózy.")

    def toggle_theme(self, enabled: bool) -> None:
        app = QtWidgets.QApplication.instance()
        if enabled:
            theme.apply_dark_theme(app)
        else:
            theme.apply_light_theme(app)

    def update_price(self) -> int:
        diagnostics = [name for name, chk in self.diagnostic_checks.items() if chk.isChecked()]
        price = pricing.calculate_price(
            self.locality_combo.currentText(),
            self.treatment_spin.value(),
            self.heavy_check.isChecked(),
            diagnostics,
        )
        self.price_label.setText(f"Cena: {price} Kč")
        return price

    def copy_report(self) -> None:
        QtGui.QGuiApplication.clipboard().setText(self.result_box.toPlainText())

    def export_report(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Uložit zprávu", filter="Text files (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.result_box.toPlainText())

    def generate_tags(self, mkn: str, diagnosis: str, locality: str) -> list[str]:
        return [
            mkn.lower(),
            diagnosis.replace(" ", "").lower(),
            locality.replace(" ", "").lower(),
        ]

    def generate_report(self) -> None:
        diag = self.diagnosis_edit.text().strip()
        mkn = self.mkn_edit.text().strip()
        locality = self.locality_combo.currentText()

        price = self.update_price()
        tags = self.generate_tags(mkn, diag, locality)

        anam = {sec: self.fields[sec].toPlainText().strip() or "..." for sec in ANAM_SECTIONS}
        status = {sec: self.fields[sec].toPlainText().strip() or "..." for sec in STATUS_SECTIONS}
        examination = self.fields[EXAM_SECTIONS[0]].toPlainText().strip() or "..."
        therapy = self.fields[EXAM_SECTIONS[1]].toPlainText().strip() or "..."

        data = {
            "diagnosis": diag,
            "mkn": mkn,
            "tags": tags,
            "price": price,
            "anamnesis": anam,
            "status": status,
            "examination": examination,
            "therapy": therapy,
        }
        report = report_generator.generate_report(data)
        self.result_box.setPlainText(report)
        self.copy_report()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ReportGenerator()
    window.resize(600, 800)
    window.show()
    sys.exit(app.exec())
