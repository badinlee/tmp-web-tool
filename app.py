import sys
import fitz  # PyMuPDF
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
                             QDateEdit, QTimeEdit, QComboBox, QCheckBox, 
                             QPushButton, QTabWidget, QFileDialog, QScrollArea,
                             QMessageBox, QGroupBox, QGridLayout)
from PyQt6.QtCore import QDate, Qt

# --- RISK DATABASE (Ported from your JS) ---
RISK_LIBRARY = {
    "lvr": {
        "hazard": "Low Volume Rural (LVR)", 
        "score": 25, 
        "controls": "Use extended tapers. TSL mandatory. Positive traffic control required if sight distance is poor.", 
        "res": 6
    },
    "live_lane": {
        "hazard": "Worker Exposure in Live Lanes", 
        "score": 25, 
        "controls": "Isolate work area. Safety spotter for workers on foot. High-vis PPE mandatory.", 
        "res": 9
    },
    "height": {
        "hazard": "Overhead Services / Height", 
        "score": 15, 
        "controls": "Maintain 4m approach distance (MAD). Dedicated spotter for plant. Permit-to-dig if underground.", 
        "res": 4
    },
    "pedestrian": {
        "hazard": "Pedestrian Interface", 
        "score": 16, 
        "controls": "Physical barriers (cone bars). Safe alternative route. Accessible for wheelchairs/prams.", 
        "res": 4
    },
    "machinery": {
        "hazard": "Plant & Machinery", 
        "score": 16, 
        "controls": "360-degree checks. Spotter for reversing. Competent operators only.", 
        "res": 4
    },
    "stopgo": {
        "hazard": "Stop-Go Traffic Control", 
        "score": 16, 
        "controls": "Maintain safety zones. Adequate sight distance. Clear radio comms between MTCs.", 
        "res": 6
    }
}

class TMPGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traffic Safe TMP Generator")
        self.setGeometry(100, 100, 1000, 800)
        self.tmd_image_path = None

        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)

        # Header
        header = QLabel("Rapid TMP Generator - NZGTTM Standard")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #2563eb; margin-bottom: 10px;")
        self.layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Init Tabs
        self.init_general_tab()
        self.init_risk_tab()
        self.init_diagram_tab()

        # Generate Button
        btn_generate = QPushButton("GENERATE PDF")
        btn_generate.setFixedHeight(50)
        btn_generate.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; font-size: 16px;")
        btn_generate.clicked.connect(self.generate_pdf)
        self.layout.addWidget(btn_generate)

    def init_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # --- Presets ---
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Quick Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Select Preset...", "Pole Maintenance", "Transformer Replacement", "Geotech Drilling"])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)

        # --- Form Grid ---
        grid = QGridLayout()
        
        # Row 1
        grid.addWidget(QLabel("TMP Reference:"), 0, 0)
        self.inp_ref = QLineEdit()
        grid.addWidget(self.inp_ref, 0, 1)

        grid.addWidget(QLabel("Road Name:"), 0, 2)
        self.inp_road = QLineEdit()
        grid.addWidget(self.inp_road, 0, 3)

        # Row 2
        grid.addWidget(QLabel("Start Date:"), 1, 0)
        self.inp_start_date = QDateEdit(calendarPopup=True)
        self.inp_start_date.setDate(QDate.currentDate())
        grid.addWidget(self.inp_start_date, 1, 1)

        grid.addWidget(QLabel("End Date:"), 1, 2)
        self.inp_end_date = QDateEdit(calendarPopup=True)
        self.inp_end_date.setDate(QDate.currentDate())
        grid.addWidget(self.inp_end_date, 1, 3)

        # Row 3
        grid.addWidget(QLabel("Activity Description:"), 2, 0)
        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(60)
        grid.addWidget(self.inp_desc, 2, 1, 1, 3) # Span 3 cols

        # Row 4
        grid.addWidget(QLabel("Plant Required:"), 3, 0)
        self.inp_plant = QLineEdit()
        grid.addWidget(self.inp_plant, 3, 1, 1, 3)

        layout.addLayout(grid)
        layout.addStretch()
        self.tabs.addTab(tab, "1. General Details")

    def init_risk_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lbl = QLabel("Select Applicable Hazards (Auto-fills Risk Assessment)")
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)

        # Checkboxes
        self.risk_checks = {}
        for key, data in RISK_LIBRARY.items():
            cb = QCheckBox(data["hazard"])
            self.risk_checks[key] = cb
            layout.addWidget(cb)

        layout.addStretch()
        self.tabs.addTab(tab, "2. Risk Assessment")

    def init_diagram_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lbl = QLabel("Upload Traffic Management Diagram (Image)")
        layout.addWidget(lbl)

        btn_upload = QPushButton("Select Image File (JPG/PNG)")
        btn_upload.clicked.connect(self.upload_image)
        layout.addWidget(btn_upload)

        self.lbl_image_status = QLabel("No image selected")
        layout.addWidget(self.lbl_image_status)

        layout.addStretch()
        self.tabs.addTab(tab, "3. Diagram")

    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Diagram", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            self.tmd_image_path = file_name
            self.lbl_image_status.setText(f"Selected: {file_name.split('/')[-1]}")

    def apply_preset(self, text):
        # Auto-fill logic based on your previous presets
        if text == "Pole Maintenance":
            self.inp_desc.setText("Undertaking pole maintenance along road corridor. Replacing HV/LV pins.")
            self.inp_plant.setText("Bucket Trucks, Utes")
            self.risk_checks['lvr'].setChecked(True)
            self.risk_checks['live_lane'].setChecked(True)
            self.risk_checks['height'].setChecked(True)
        elif text == "Geotech Drilling":
            self.inp_desc.setText("Drilling Borehole in loading bay.")
            self.inp_plant.setText("Drill Rig, Ute")
            self.risk_checks['pedestrian'].setChecked(True)
            self.risk_checks['machinery'].setChecked(True)
            self.risk_checks['lvr'].setChecked(False)

    def generate_pdf(self):
        try:
            # 1. Open Template
            doc = fitz.open("template.pdf")
            page1 = doc[0]  # First page (0-index)

            # 2. Define Text Insertion Helper
            # You must MEASURE your PDF to find these x, y coordinates
            def insert_text(page, text, x, y, size=11):
                page.insert_text((x, y), str(text), fontsize=size, fontname="helv", color=(0, 0, 0))

            # 3. Insert General Data (Coordinates are EXAMPLES - You need to adjust them)
            insert_text(page1, self.inp_ref.text(), 450, 100)  # Top Right Ref
            insert_text(page1, self.inp_road.text(), 50, 250)  # Road Name Table
            insert_text(page1, self.inp_desc.toPlainText(), 50, 400) # Desc
            
            # Dates
            s_date = self.inp_start_date.date().toString("dd/MM/yyyy")
            insert_text(page1, s_date, 150, 300)

            # 4. Insert Risk Assessment Data
            # Assuming Risk Assessment is on Page 7 (Index 6)
            if len(doc) > 6:
                risk_page = doc[6]
                y_pos = 200 # Starting Y position for the table
                
                # Default "Site Establishment" Risk
                insert_text(risk_page, "Site Establishment", 50, y_pos)
                insert_text(risk_page, "16", 200, y_pos)
                insert_text(risk_page, "Standard Setup Controls...", 250, y_pos, size=9)
                y_pos += 40

                # Dynamic Risks
                for key, cb in self.risk_checks.items():
                    if cb.isChecked():
                        risk = RISK_LIBRARY[key]
                        insert_text(risk_page, risk["hazard"], 50, y_pos)
                        insert_text(risk_page, str(risk["score"]), 200, y_pos)
                        # Text wrap for controls might be needed for long text
                        insert_text(risk_page, risk["controls"], 250, y_pos, size=8)
                        y_pos += 40

            # 5. Insert Diagram (Image)
            # Assuming Diagram goes on the last page or a specific page
            if self.tmd_image_path:
                # Add a new page for the diagram if needed, or overlay on existing
                # page_diagram = doc.new_page() 
                # OR use existing:
                page_diagram = doc[-1] 
                
                # Define rect for image [x0, y0, x1, y1]
                rect = fitz.Rect(50, 100, 550, 700)
                page_diagram.insert_image(rect, filename=self.tmd_image_path)

            # 6. Save
            output_filename = f"TMP_{self.inp_ref.text()}_{datetime.now().strftime('%H%M')}.pdf"
            doc.save(output_filename)
            doc.close()

            QMessageBox.information(self, "Success", f"PDF Generated Successfully:\n{output_filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TMPGenerator()
    window.show()
    sys.exit(app.exec())