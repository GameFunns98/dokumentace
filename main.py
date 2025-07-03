from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtWidgets, QtGui, QtCore

import mkn10
import pricing
import report_generator
import theme

ANAM_SECTIONS = ["OA", "RA", "PA", "SA", "FA", "AA", "EA", "NO"]
# default texts for anamnesis sections if left empty by the user
ANAM_DEFAULTS = {
    "OA": "Bez závažné osobní anamnézy.",
    "RA": "Rodinná anamnéza bez významných odchylek.",
    "PA": "Pracovní anamnéza nevýznamná.",
    "SA": "Sociální anamnéza standardní.",
    "FA": "Dlouhodobě bez pravidelné medikace.",
    "AA": "Bez známé alergie.",
    "EA": "Epidemiologická anamnéza negativní.",
    "NO": "Bez aktuálních potíží.",
}
STATUS_SECTIONS = ["Subj.", "Obj."]
VITAL_KEYS = ["TK", "TF", "SpO2", "TT", "RF", "GCS"]
EXAM_SECTIONS = ["Vyšetření", "Terapie"]

# simple keyword based suggestions for NO field -> (keywords, code, description)
SUGGESTION_RULES = [
    (("slabost", "ztr\u00e1ta řeči"), "I63", "CMP"),
    (("jednostrann\u00e1 slabost",), "I63", "CMP"),
    (("bolest břicha",), "R10", "Bolest břicha"),
]

DATA_PATH = Path(__file__).resolve().parent / "data" / "diagnosis_children.json"


class ReportGenerator(QtWidgets.QTabWidget):
    def __init__(self) -> None:
        super().__init__()
        mkn10.load_mkn10_data(str(DATA_PATH))

        self.setWindowTitle("Generátor lékařské zprávy - Doctor-11")
        self.setMinimumSize(600, 700)
        self.fields: dict[str, QtWidgets.QTextEdit] = {}
        self.diagnostic_checks: dict[str, QtWidgets.QCheckBox] = {}
        self.device_checks: dict[str, QtWidgets.QCheckBox] = {}
        self.current_tox_therapy = ""
        self.suggested_code = ""
        self.suggested_desc = ""
        self.current_vital_desc = ""
        self.init_ui()
        self.update_price()

    # -------------------- UI setup --------------------
    def init_ui(self) -> None:
        form_tab = QtWidgets.QWidget()
        form_layout = QtWidgets.QVBoxLayout(form_tab)
        form_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_layout.addWidget(scroll_area)

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

        # -------------------- Vital signs --------------------
        vital_box = QtWidgets.QGroupBox("Vitální funkce")
        vital_form = QtWidgets.QFormLayout()
        bp_layout = QtWidgets.QHBoxLayout()
        self.bp_sys_edit = QtWidgets.QLineEdit()
        self.bp_dia_edit = QtWidgets.QLineEdit()
        self.bp_sys_edit.textChanged.connect(self.update_vitals_interpretation)
        self.bp_dia_edit.textChanged.connect(self.update_vitals_interpretation)
        bp_layout.addWidget(self.bp_sys_edit)
        bp_layout.addWidget(QtWidgets.QLabel("/"))
        bp_layout.addWidget(self.bp_dia_edit)
        bp_widget = QtWidgets.QWidget()
        bp_widget.setLayout(bp_layout)
        vital_form.addRow("TK (mmHg):", bp_widget)

        self.hr_edit = QtWidgets.QLineEdit()
        self.hr_edit.textChanged.connect(self.update_vitals_interpretation)
        vital_form.addRow("TF (/min):", self.hr_edit)

        self.spo2_edit = QtWidgets.QLineEdit()
        self.spo2_edit.textChanged.connect(self.update_vitals_interpretation)
        vital_form.addRow("SpO2 (%):", self.spo2_edit)

        self.temp_edit = QtWidgets.QLineEdit()
        self.temp_edit.textChanged.connect(self.update_vitals_interpretation)
        vital_form.addRow("TT (°C):", self.temp_edit)

        self.resp_edit = QtWidgets.QLineEdit()
        self.resp_edit.textChanged.connect(self.update_vitals_interpretation)
        vital_form.addRow("RF (/min):", self.resp_edit)

        self.gcs_spin = QtWidgets.QSpinBox()
        self.gcs_spin.setRange(3, 15)
        self.gcs_spin.valueChanged.connect(self.update_vitals_interpretation)
        vital_form.addRow("GCS:", self.gcs_spin)

        gcs_calc = QtWidgets.QGroupBox("GCS kalkulačka")
        gcs_form = QtWidgets.QFormLayout()
        self.gcs_eye_spin = QtWidgets.QSpinBox()
        self.gcs_eye_spin.setRange(1, 4)
        self.gcs_eye_spin.setValue(4)
        self.gcs_verbal_spin = QtWidgets.QSpinBox()
        self.gcs_verbal_spin.setRange(1, 5)
        self.gcs_verbal_spin.setValue(5)
        self.gcs_motor_spin = QtWidgets.QSpinBox()
        self.gcs_motor_spin.setRange(1, 6)
        self.gcs_motor_spin.setValue(6)
        for sp in (self.gcs_eye_spin, self.gcs_verbal_spin, self.gcs_motor_spin):
            sp.valueChanged.connect(self.update_gcs_from_calc)
        gcs_form.addRow("Oko:", self.gcs_eye_spin)
        gcs_form.addRow("Slovo:", self.gcs_verbal_spin)
        gcs_form.addRow("Pohyb:", self.gcs_motor_spin)
        self.gcs_total_label = QtWidgets.QLabel("15")
        gcs_form.addRow("Součet:", self.gcs_total_label)
        gcs_calc.setLayout(gcs_form)
        vital_form.addRow(gcs_calc)

        self.vital_desc_label = QtWidgets.QLabel()
        vital_form.addRow(self.vital_desc_label)

        vital_box.setLayout(vital_form)
        layout.addWidget(vital_box)

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

        # -------------------- Zdravotnické prostředky --------------------
        device_box = QtWidgets.QGroupBox("Zdravotnické prostředky")
        device_layout = QtWidgets.QHBoxLayout()
        for name in ["Monitor", "Defibrilátor", "Ambuvak", "Glukometr", "Pulsní oxymetr"]:
            chk = QtWidgets.QCheckBox(name)
            self.device_checks[name] = chk
            device_layout.addWidget(chk)
        device_box.setLayout(device_layout)
        layout.addWidget(device_box)

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
        self.load_lab_button = QtWidgets.QPushButton("Načíst z CSV/JSON")
        self.load_lab_button.clicked.connect(self.load_lab_results)
        lab_form.addRow(self.load_lab_button)
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

        self.addTab(form_tab, "Formulář")

        # -------------------- Explanations tab --------------------
        notes_tab = QtWidgets.QWidget()
        notes_layout = QtWidgets.QVBoxLayout(notes_tab)
        notes_text = QtWidgets.QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setHtml(
            "<h2>Referenční hodnoty laboratorních výsledků</h2>"
            "<ul>"
            "<li>CRP: 0–5 mg/L</li>"
            "<li>Glykémie: 3.9–7.0 mmol/L</li>"
            "<li>Laktát: 0.5–2.0 mmol/L</li>"
            "<li>pH: 7.35–7.45</li>"
            "</ul>"
            "<h2>Základní EKG nálezy</h2>"
            "<ul>"
            "<li>Tachykardie</li>"
            "<li>Bradykardie</li>"
            "<li>Fibrilace síní</li>"
            "<li>STEMI</li>"
            "</ul>"
            "<h2>Zkratky</h2>"
            "<ul>"
            "<li>OA – osobní anamnéza</li>"
            "<li>RA – rodinná anamnéza</li>"
            "<li>PA – pracovní anamnéza</li>"
            "<li>SA – sociální anamnéza</li>"
            "<li>FA – farmakologická anamnéza</li>"
            "<li>AA – alergologická anamnéza</li>"
            "<li>EA – epidemiologická anamnéza</li>"
            "<li>NO – nynější onemocnění</li>"
            "</ul>"
        )
        notes_layout.addWidget(notes_text)
        self.addTab(notes_tab, "Vysvětlivky")

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

    def load_lab_results(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Načíst laboratorní výsledky",
            filter="Data files (*.csv *.json)"
        )
        if not path:
            return
        try:
            if path.lower().endswith(".json"):
                import json
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            else:
                import csv
                with open(path, newline="", encoding="utf-8") as fh:
                    reader = csv.DictReader(fh)
                    data = next(reader)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Chyba", "Nelze načíst soubor")
            return
        self.crp_edit.setText(str(data.get("CRP", "")))
        self.glucose_edit.setText(str(data.get("Glykémie", data.get("Glucose", ""))))
        self.lactate_edit.setText(str(data.get("Laktát", "")))
        self.ph_edit.setText(str(data.get("pH", "")))
        self.update_lab_interpretation()

    def update_vitals_interpretation(self) -> None:
        msgs: list[str] = []
        try:
            spo = float(self.spo2_edit.text().replace(',', '.'))
            if spo < 90:
                msgs.append("Saturace nízká")
                self.spo2_edit.setStyleSheet("background-color: salmon")
            else:
                self.spo2_edit.setStyleSheet("")
        except ValueError:
            self.spo2_edit.setStyleSheet("")
        try:
            hr = float(self.hr_edit.text().replace(',', '.'))
            if hr > 100:
                msgs.append("Tepová frekvence zvýšená")
                self.hr_edit.setStyleSheet("background-color: salmon")
            else:
                self.hr_edit.setStyleSheet("")
        except ValueError:
            self.hr_edit.setStyleSheet("")
        self.current_vital_desc = "; ".join(msgs)
        self.vital_desc_label.setText(self.current_vital_desc)

    def update_gcs_from_calc(self) -> None:
        total = self.gcs_eye_spin.value() + self.gcs_verbal_spin.value() + self.gcs_motor_spin.value()
        self.gcs_spin.setValue(total)
        self.gcs_total_label.setText(str(total))

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

        anam = {
            sec: self.fields[sec].toPlainText().strip() or ANAM_DEFAULTS[sec]
            for sec in ANAM_SECTIONS
        }
        status = {sec: self.fields[sec].toPlainText().strip() or "..." for sec in STATUS_SECTIONS}
        examination = self.fields[EXAM_SECTIONS[0]].toPlainText().strip() or "..."
        therapy = self.fields[EXAM_SECTIONS[1]].toPlainText().strip() or "..."

        vitals = {
            "TK": f"{self.bp_sys_edit.text()}/{self.bp_dia_edit.text()}",
            "TF": self.hr_edit.text(),
            "SpO2": self.spo2_edit.text(),
            "TT": self.temp_edit.text(),
            "RF": self.resp_edit.text(),
            "GCS": str(self.gcs_spin.value()),
        }

        data = {
            "diagnosis": diag,
            "mkn": mkn,
            "tags": tags,
            "price": price,
            "anamnesis": anam,
            "status": status,
            "vitals": {"values": vitals, "desc": self.current_vital_desc},
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
