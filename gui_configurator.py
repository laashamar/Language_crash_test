from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QSpinBox, QPushButton, QTextEdit, QFileDialog, QMessageBox, QSplitter,
    QDoubleSpinBox, QTabWidget, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QObject, QThread, Signal
from PySide6.QtGui import QTextCursor, QFont
import sys
import logging
from io import StringIO
from pathlib import Path
from generator import generate_messages
from config import Config
import copilot_ui_stress_test  # Importer for å kunne kjøre testen

# --- NY ARBEIDERKLASSE FOR STRESSTEST ---
class StressTestWorker(QObject):
    """Kjører stresstesten i en separat tråd for å unngå at GUI-en fryser."""
    progress = Signal(str)  # Signal for å sende loggmeldinger
    finished = Signal()     # Signal for når testen er ferdig

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        """Hovedmetoden som kjører testen."""
        try:
            # Sett opp en midlertidig logger for å fange output fra stresstesten
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # Bruk root logger for å fange alt
            logger = logging.getLogger()
            original_level = logger.level
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)

            # Sett konfigurasjonen for testmodulen
            copilot_ui_stress_test.set_config(self.config)
            
            # Start selve testen
            copilot_ui_stress_test.main()

            # Hent og send logg-output
            log_contents = log_stream.getvalue()
            self.progress.emit(log_contents)

            # Gjenopprett logger
            logger.removeHandler(handler)
            logger.setLevel(original_level)

        except Exception as e:
            self.progress.emit(f"❌ En kritisk feil oppstod under testen: {e}\n")
        finally:
            self.finished.emit()


class Configurator(QWidget):
    """Enhanced GUI configurator with scrollable output field and config integration."""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setWindowTitle("Copilot UI Stress Test Configurator")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.thread = None  # Holder referanse til arbeidstråden
        
    def setup_ui(self):
        # ... (resten av UI-koden er uendret)
        # Create splitter for upper config and lower output
        splitter = QSplitter(Qt.Vertical)
        
        # Upper half: Configuration tabs
        config_widget = QTabWidget()
        
        # Basic configuration tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Configuration from Config class
        config_group = QGroupBox("📊 Test Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Number of messages
        config_layout.addWidget(QLabel("✍️ Number of messages:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 1000)
        self.spin_count.setValue(self.config.number_of_messages)
        self.spin_count.valueChanged.connect(self.show_preview)
        config_layout.addWidget(self.spin_count)
        
        # Wait time between messages
        config_layout.addWidget(QLabel("⏱️ Wait time between messages (seconds):"))
        self.spin_wait = QDoubleSpinBox()
        self.spin_wait.setRange(0.1, 10.0)
        self.spin_wait.setSingleStep(0.1)
        self.spin_wait.setValue(self.config.wait_time_seconds)
        config_layout.addWidget(self.spin_wait)
        
        basic_layout.addWidget(config_group)
        
        # Language selection (legacy from original)
        lang_group = QGroupBox("🔍 Language Mode")
        lang_layout = QVBoxLayout(lang_group)
        
        self.radio_os = QRadioButton("Follow OS language (recommended)")
        self.radio_eng = QRadioButton("English only")
        self.radio_both = QRadioButton("Both languages")
        self.radio_os.setChecked(True)
        
        lang_layout.addWidget(self.radio_os)
        lang_layout.addWidget(self.radio_eng)
        lang_layout.addWidget(self.radio_both)
        basic_layout.addWidget(lang_group)
        
        # Preview section
        preview_group = QGroupBox("🧪 Message Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(150)
        preview_layout.addWidget(self.preview)
        
        self.btn_preview = QPushButton("Generate Preview")
        self.btn_preview.clicked.connect(self.show_preview)
        preview_layout.addWidget(self.btn_preview)
        
        basic_layout.addWidget(preview_group)
        basic_layout.addStretch()
        
        config_widget.addTab(basic_tab, "Basic Config")
        
        # Advanced configuration tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Window patterns
        window_group = QGroupBox("🪟 Window Detection")
        window_layout = QVBoxLayout(window_group)
        
        window_layout.addWidget(QLabel("Window title regex:"))
        self.edit_window_regex = QTextEdit()
        self.edit_window_regex.setMaximumHeight(60)
        self.edit_window_regex.setPlainText(self.config.window_title_regex)
        window_layout.addWidget(self.edit_window_regex)
        
        advanced_layout.addWidget(window_group)
        
        # Debugging settings
        debug_group = QGroupBox("⚙️ Debugging Settings")
        debug_layout = QVBoxLayout(debug_group)

        debug_layout.addWidget(QLabel("Debug script timeout (seconds):"))
        self.spin_debug_timeout = QSpinBox()
        self.spin_debug_timeout.setRange(10, 120)
        self.spin_debug_timeout.setValue(self.config.debug_output_timeout)

        tooltip_text = """
        Sets how long the script waits for the UI analysis to complete.
        Increase this on slower computers.

        Anbefalinger:
        - Ny CPU, 16GB RAM: 20-30 sekunder
        - ~5 år gammel CPU, 8GB RAM: 30-45 sekunder
        - Eldre CPU, 4GB RAM: 45-60 sekunder
        """
        self.spin_debug_timeout.setToolTip(tooltip_text.strip())
        debug_layout.addWidget(self.spin_debug_timeout)

        advanced_layout.addWidget(debug_group)
        
        advanced_layout.addStretch()
        
        config_widget.addTab(advanced_tab, "Advanced")
        
        # Add config widget to splitter (upper half)
        splitter.addWidget(config_widget)
        
        # Lower half: Runtime output and logs
        output_group = QGroupBox("📄 Runtime Output & Logs")
        output_layout = QVBoxLayout(output_group)
        
        # Scrollable output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 10))
        self.output_area.setPlainText("Ready to start stress testing...\n")
        output_layout.addWidget(self.output_area)
        
        # Output controls
        output_controls = QHBoxLayout()
        self.btn_clear_output = QPushButton("Clear Output")
        self.btn_clear_output.clicked.connect(self.clear_output)
        self.btn_save_log = QPushButton("Save Log")
        self.btn_save_log.clicked.connect(self.save_log)
        output_controls.addWidget(self.btn_clear_output)
        output_controls.addWidget(self.btn_save_log)
        output_controls.addStretch()
        output_layout.addLayout(output_controls)
        
        splitter.addWidget(output_group)
        
        # Set splitter sizes (60% config, 40% output)
        splitter.setSizes([360, 240])
        
        main_layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.btn_save_config = QPushButton("💾 Save Config")
        self.btn_save_config.clicked.connect(self.save_config)
        
        self.btn_load_config = QPushButton("📂 Load Config")
        self.btn_load_config.clicked.connect(self.load_config)
        
        self.btn_start = QPushButton("✅ Start Test")
        self.btn_start.clicked.connect(self.start_test)
        
        self.btn_export = QPushButton("📁 Export Messages")
        self.btn_export.clicked.connect(self.export_messages)
        
        button_layout.addWidget(self.btn_save_config)
        button_layout.addWidget(self.btn_load_config)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_export)
        button_layout.addWidget(self.btn_start)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Initial preview
        self.show_preview()

    # --- START_TEST ER HELT OMSKREVET ---
    def start_test(self):
        """Starter stresstesten i en bakgrunnstråd."""
        self.btn_start.setEnabled(False)  # Deaktiver knappen for å unngå flere trykk
        self.append_output("=" * 50 + "\n")
        self.append_output("🚀 Initialiserer stresstest...\n")
        
        # 1. Hent nåværende konfigurasjon
        config = self.get_current_config()
        
        # 2. Sett opp tråd og arbeider
        self.thread = QThread()
        self.worker = StressTestWorker(config)
        self.worker.moveToThread(self.thread)
        
        # 3. Koble signaler og slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.append_output)
        self.worker.finished.connect(self.on_test_finished) # Koble til en ny metode for opprydding
        
        # 4. Start tråden
        self.thread.start()

    def on_test_finished(self):
        """Kalles når bakgrunnstråden er ferdig."""
        self.append_output("🎉 Testen er fullført.\n")
        self.btn_start.setEnabled(True)  # Aktiver knappen igjen
        QMessageBox.information(self, "Test Fullført", "Stresstesten er ferdig.")

    def append_output(self, text):
        """Legger til tekst i output-området."""
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()

    def clear_output(self):
        """Tømmer output-området."""
        self.output_area.clear()
        self.append_output("Output tømt.\n")

    # ... (alle andre metoder fra get_current_config og nedover er uendret) ...
    def save_log(self, *args, **kwargs):
        """Save the current output to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "stress_test_log.txt", "Text files (*.txt)"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.output_area.toPlainText())
            self.append_output(f"Log saved to {filename}\n")

    def get_current_config(self, *args, **kwargs):
        """Get current configuration from UI and regenerate messages."""
        config = Config()
        config.number_of_messages = self.spin_count.value()
        config.wait_time_seconds = self.spin_wait.value()
        config.window_title_regex = self.edit_window_regex.toPlainText().strip()
        config.debug_output_timeout = self.spin_debug_timeout.value()
        
        # Regenerate sample messages to match the final count before saving/running
        config.regenerate_sample_messages()
        
        return config

    def load_config_to_ui(self, *args, **kwargs):
        config = args[0] if args else kwargs.get('config')
        """Load configuration into UI."""
        self.spin_count.setValue(config.number_of_messages)
        self.spin_wait.setValue(config.wait_time_seconds)
        self.edit_window_regex.setPlainText(config.window_title_regex)
        self.spin_debug_timeout.setValue(config.debug_output_timeout)

    def save_config(self, *args, **kwargs):
        """Save current configuration to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "config.json", "JSON files (*.json)"
        )
        if filename:
            try:
                config = self.get_current_config()
                config.save_to_file(filename)
                self.append_output(f"Configuration saved to {filename}\n")
                QMessageBox.information(self, "Success", f"Configuration saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def load_config(self, *args, **kwargs):
        """Load configuration from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON files (*.json)"
        )
        if filename:
            try:
                config = Config.load_from_file(filename)
                self.load_config_to_ui(config)
                self.config = config
                self.append_output(f"Configuration loaded from {filename}\n")
                QMessageBox.information(self, "Success", f"Configuration loaded from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {e}")

    def get_language_mode(self, *args, **kwargs):
        """Get selected language mode."""
        if self.radio_os.isChecked():
            return "os"
        elif self.radio_eng.isChecked():
            return "english"
        else:
            return "both"

    def show_preview(self, *args, **kwargs):
        """
        Update the internal config, regenerate messages based on the current
        UI value, and show a preview.
        """
        try:
            # Update the internal config object with the current value from the UI
            current_count = self.spin_count.value()
            self.config.number_of_messages = current_count
            
            # Regenerate the messages based on the new count
            self.config.regenerate_sample_messages()
            
            # Show a small subset of the newly generated messages in the preview
            preview_count = min(5, current_count)
            preview_messages = self.config.sample_messages[:preview_count]
            
            self.preview.setPlainText("\n".join(preview_messages))
            self.append_output(f"Preview updated for {current_count} messages.\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate preview: {e}")

    def export_messages(self, *args, **kwargs):
        """Export generated messages to file."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Messages", "messages.txt", "Text files (*.txt)"
            )
            if filename:
                count = self.spin_count.value()
                messages = generate_messages(count)
                with open(filename, 'w', encoding='utf-8') as f:
                    for i, msg in enumerate(messages, 1):
                        f.write(f"{i:03d}: {msg}\n")
                
                self.append_output(f"Exported {count} messages to {filename}\n")
                QMessageBox.information(self, "Success", f"Exported {count} messages to {filename}")
                
        except Exception as e:
            self.append_output(f"Error exporting messages: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed to export messages: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Configurator()
    window.show()
    sys.exit(app.exec())

