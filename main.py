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

# simple keyword based suggestions for NO field -> (keywords, code, description)
SUGGESTION_RULES = [
    (("slabost", "řeč"), "I63", "CMP"),
    (("bolest břicha",), "R10", "Bolest břicha"),
]

DATA_PATH = Path(__file__).resolve().parent / "data" / "diagnosis_children.json"


class ReportGenerator(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        mkn10.load_mkn10_data(str(DATA_PATH))

        self.setWindowTitle("Generátor lékařské zprávy - Doctor-11")
        self.setMinimumSize(600, 700)
        self.fields: dict[str, QtWidgets.QTextEdit] = {}
        self.diagnostic_checks: dict[str, QtWidgets.QCheckBox] = {}
        self.current_tox_therapy = ""
        self.suggested_code = ""
        self.suggested_desc = ""
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
            if section == "NO":
                text.textChanged.connect(self.analyze_no)
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

        # -------------------- Laboratory results --------------------
        lab_box = QtWidgets.QGroupBox("Laboratorní hodnoty")
        lab_form = QtWidgets.QFormLayout()
        self.crp_edit = QtWidgets.QLineEdit()
        self.crp_edit.textChanged.connect(self.update_lab_interpretation)
        lab_form.addRow("CRP (mg/L):", self.crp_edit)
        self.glucose_edit = QtWidgets.QLineEdit()
        self.glucose_edit.textChanged.connect(self.update_lab_interpretation)
        lab_form.addRow("Glykémie (mmol/L):", self.glucose_edit)
        self.lactate_edit = QtWidgets.QLineEdit()
        self.lactate_edit.textChanged.connect(self.update_lab_interpretation)
        lab_form.addRow("Laktát (mmol/L):", self.lactate_edit)
        self.ph_edit = QtWidgets.QLineEdit()
        self.ph_edit.textChanged.connect(self.update_lab_interpretation)
        lab_form.addRow("pH:", self.ph_edit)
        self.lab_interpret_label = QtWidgets.QLabel()
        lab_form.addRow(self.lab_interpret_label)
        lab_box.setLayout(lab_form)
        layout.addWidget(lab_box)

        # -------------------- Toxicology --------------------
        tox_box = QtWidgets.QGroupBox("Toxikologie")
        tox_form = QtWidgets.QFormLayout()
        self.tox_substance = QtWidgets.QComboBox()
        self.tox_substance.setEditable(True)
        self.tox_substance.addItems(["alkohol", "benzo", "opioid", "CO", "pesticidy"])
        self.tox_substance.editTextChanged.connect(self.update_toxicology_interpretation)
        self.tox_substance.currentTextChanged.connect(self.update_toxicology_interpretation)
        tox_form.addRow("Látka:", self.tox_substance)
        self.tox_dose = QtWidgets.QLineEdit()
        self.tox_dose.textChanged.connect(self.update_toxicology_interpretation)
        tox_form.addRow("Odhadovaná dávka:", self.tox_dose)
        self.tox_time = QtWidgets.QLineEdit()
        self.tox_time.textChanged.connect(self.update_toxicology_interpretation)
        tox_form.addRow("Čas expozice (HH:MM):", self.tox_time)
        self.tox_route = QtWidgets.QComboBox()
        self.tox_route.addItems(["per os", "inhalace", "i.v.", "neznámý"])
        self.tox_route.currentTextChanged.connect(self.update_toxicology_interpretation)
        tox_form.addRow("Způsob expozice:", self.tox_route)
        self.tox_symptoms = QtWidgets.QTextEdit()
        self.tox_symptoms.setMinimumHeight(60)
        self.tox_symptoms.textChanged.connect(self.update_toxicology_interpretation)
        tox_form.addRow("Klinické příznaky:", self.tox_symptoms)
        self.tox_interpret_label = QtWidgets.QLabel()
        self.tox_therapy_label = QtWidgets.QLabel()
        self.tox_therapy_label.setWordWrap(True)
        tox_form.addRow(self.tox_interpret_label)
        tox_form.addRow("Doporučená terapie:", self.tox_therapy_label)
        self.tox_add_button = QtWidgets.QPushButton("Přidat do terapie")
        self.tox_add_button.clicked.connect(self.add_tox_therapy)
        tox_form.addRow(self.tox_add_button)
        tox_box.setLayout(tox_form)
        layout.addWidget(tox_box)

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
        self.suggest_label = QtWidgets.QLabel()
        self.suggest_button = QtWidgets.QPushButton("Použít návrh")
        self.suggest_button.clicked.connect(self.apply_diag_suggestion)
        self.suggest_label.hide()
        self.suggest_button.hide()
        diag_form.addRow(self.suggest_label, self.suggest_button)
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

    # -------------------- Intelligent helpers --------------------
    def analyze_no(self) -> None:
        text = self.fields["NO"].toPlainText().lower()
        suggestion = None
        for keywords, code, desc in SUGGESTION_RULES:
            if all(k in text for k in keywords):
                suggestion = (code, desc)
                break
        if suggestion:
            self.suggested_code, self.suggested_desc = suggestion
            self.suggest_label.setText(f"Návrh diagnózy: {suggestion[0]} – {suggestion[1]}")
            self.suggest_label.show()
            self.suggest_button.show()
        else:
            self.suggest_label.hide()
            self.suggest_button.hide()

    def apply_diag_suggestion(self) -> None:
        if self.suggested_code:
            self.mkn_edit.setText(self.suggested_code)
            self.diagnosis_edit.setText(self.suggested_desc)
        self.suggest_label.hide()
        self.suggest_button.hide()

    def update_lab_interpretation(self) -> None:
        msgs: list[str] = []
        try:
            crp = float(self.crp_edit.text().replace(",", "."))
            if crp > 5:
                msgs.append("Zvýšené CRP – známka zánětu")
        except ValueError:
            pass
        try:
            gly = float(self.glucose_edit.text().replace(",", "."))
            if gly < 3.9:
                msgs.append("Hypoglykémie")
            elif gly > 7.0:
                msgs.append("Hyperglykémie")
        except ValueError:
            pass
        try:
            lac = float(self.lactate_edit.text().replace(",", "."))
            if lac > 2.0:
                msgs.append("Laktátová acidóza")
        except ValueError:
            pass
        try:
            ph_val = float(self.ph_edit.text().replace(",", "."))
            if ph_val < 7.35:
                msgs.append("Acidóza")
            elif ph_val > 7.45:
                msgs.append("Alkalóza")
        except ValueError:
            pass
        self.lab_interpret_label.setText("; ".join(msgs))

    def update_toxicology_interpretation(self) -> None:
        substance = self.tox_substance.currentText().lower()
        symptoms = self.tox_symptoms.toPlainText().lower()
        dose_text = self.tox_dose.text().replace(",", ".")
        dose_val = None
        try:
            dose_val = float("".join(ch for ch in dose_text if ch.isdigit() or ch == "."))
        except ValueError:
            pass

        msgs: list[str] = []
        therapy: list[str] = []
        if "opioid" in substance and ("mioz" in symptoms or "poruch" in symptoms):
            msgs.append("Podezření na opioidní intoxikaci – zvážit podání Naloxonu")
            therapy.append("Naloxon")
        if "alkohol" in substance and dose_val is not None and dose_val > 3:
            msgs.append("Závažná etanolová intoxikace – monitorace, glukóza, thiamin, hydratace")
            therapy.append("monitorace, glukóza, thiamin, hydratace")
        if "co" == substance or substance.startswith("co "):
            msgs.append("Zvážit hyperbarickou komoru, 100% kyslík")
            therapy.append("hyperbarická komora, 100% kyslík")

        base = ["výplach žaludku (do 1h)", "aktivní uhlí 1g/kg", "antidota (naloxon, flumazenil, NAC...)"]
        therapy.extend(base)

        self.tox_interpret_label.setText("; ".join(msgs))
        self.current_tox_therapy = "\n".join(therapy)
        self.tox_therapy_label.setText(self.current_tox_therapy)

    def add_tox_therapy(self) -> None:
        if not self.current_tox_therapy:
            return
        current = self.fields[EXAM_SECTIONS[1]].toPlainText()
        if current and not current.endswith("\n"):
            current += "\n"
        self.fields[EXAM_SECTIONS[1]].setPlainText(current + self.current_tox_therapy)

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
