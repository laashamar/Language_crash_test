from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QSpinBox, QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
import sys
from generator import generate_messages

class Configurator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Copilot UI Stress Test Configurator")
        self.setMinimumSize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Språkvalg
        layout.addWidget(QLabel("🔍 Velg språk for knappesøk:"))
        self.radio_os = QRadioButton("Følg OS-språk (anbefalt)")
        self.radio_eng = QRadioButton("Kun engelske uttrykk")
        self.radio_both = QRadioButton("Begge språk")
        self.radio_os.setChecked(True)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(self.radio_os)
        lang_layout.addWidget(self.radio_eng)
        lang_layout.addWidget(self.radio_both)
        layout.addLayout(lang_layout)

        # Antall meldinger
        layout.addWidget(QLabel("✍️ Antall meldinger som skal genereres:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(10, 500)
        self.spin_count.setValue(50)
        layout.addWidget(self.spin_count)

        # Eksempelvisning
        layout.addWidget(QLabel("🧪 Eksempel på genererte meldinger:"))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)

        # Knapp for å generere eksempel
        self.btn_preview = QPushButton("Generer eksempel")
        self.btn_preview.clicked.connect(self.show_preview)
        layout.addWidget(self.btn_preview)

        # Start og eksport
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("✅ Start test")
        self.btn_start.clicked.connect(self.start_test)
        self.btn_export = QPushButton("📁 Eksporter meldinger")
        self.btn_export.clicked.connect(self.export_messages)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_language_mode(self):
        if self.radio_os.isChecked():
            return "os"
        elif self.radio_eng.isChecked():
            return "english"
        else:
            return "both"

    def show_preview(self):
        count = min(5, self.spin_count.value())
        messages = generate_messages(count)
        self.preview.setPlainText("\n".join(messages))

    def start_test(self):
        lang_mode = self.get_language_mode()
        count = self.spin_count.value()
        QMessageBox.information(self, "Startet", f"Starter test med språkmodus: {lang_mode}, antall meldinger: {count}")
        # Her kan du sende config videre til stress-test-skriptet

    def export_messages(self):
        messages = generate_messages(self.spin_count.value())
        path, _ = QFileDialog.getSaveFileName(self, "Lagre meldinger", "meldinger.txt", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(messages))
            QMessageBox.information(self, "Lagret", f"Meldinger lagret til:\n{path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Configurator()
    window.show()
    sys.exit(app.exec())