from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QTextEdit, QFileDialog, QMessageBox, QSplitter,
    QDoubleSpinBox, QTabWidget, QGroupBox
)
from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QTextCursor, QFont
import sys
import contextlib
import logging
from config import Config
import copilot_ui_stress_test

# --- HJELPEKLASSE FOR SANNTIDS LOGGING ---
class StreamToSignal(QObject):
    """En klasse som omdirigerer sys.stdout til et Qt-signal."""
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass

# --- OPPDATERT ARBEIDERKLASSE ---
class StressTestWorker(QObject):
    """Kjører stresstesten i en separat tråd med sanntids-output."""
    progress = Signal(str)
    finished = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.result = {}

    def run(self):
        """Hovedmetoden som kjører testen."""
        stdout_redirector = StreamToSignal()
        stdout_redirector.text_written.connect(self.progress.emit)
        
        # Bruk en logger for å fange opp interne feil i testlogikken
        logger = logging.getLogger("gui_worker")
        logger.addHandler(logging.NullHandler()) # Forhindrer "No handler found"

        try:
            # Omdiriger stdout for varigheten av denne metoden
            with contextlib.redirect_stdout(stdout_redirector):
                # Kaller den refaktorerte funksjonen som returnerer et resultat
                self.result = copilot_ui_stress_test.run_stress_test_logic(self.config, logger)
        except Exception as e:
            self.progress.emit(f"❌ En kritisk feil oppstod i workeren: {e}\n")
            self.result = {'error': str(e), 'success': 0, 'total': self.config.number_of_messages}
        finally:
            self.finished.emit()


class Configurator(QWidget):
    """Forbedret GUI-konfigurator med trådsikker testkjøring."""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setWindowTitle("Copilot UI Stress Test Configurator")
        self.setMinimumSize(800, 600)
        self.thread = None
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setter opp brukergrensesnittet."""
        main_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Vertical)
        config_widget = QTabWidget()
        
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        config_group = QGroupBox("📊 Test Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.addWidget(QLabel("✍️ Number of messages:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 1000)
        self.spin_count.setValue(self.config.number_of_messages)
        self.spin_count.valueChanged.connect(self.show_preview)
        config_layout.addWidget(self.spin_count)
        config_layout.addWidget(QLabel("⏱️ Wait time between messages (seconds):"))
        self.spin_wait = QDoubleSpinBox()
        self.spin_wait.setRange(0.1, 10.0)
        self.spin_wait.setSingleStep(0.1)
        self.spin_wait.setValue(self.config.wait_time_seconds)
        config_layout.addWidget(self.spin_wait)
        basic_layout.addWidget(config_group)
        
        preview_group = QGroupBox("🧪 Message Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(150)
        preview_layout.addWidget(self.preview)
        basic_layout.addWidget(preview_group)
        basic_layout.addStretch()
        config_widget.addTab(basic_tab, "Basic Config")
        
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        window_group = QGroupBox("🪟 Window Detection")
        window_layout = QVBoxLayout(window_group)
        window_layout.addWidget(QLabel("Window title regex:"))
        self.edit_window_regex = QTextEdit()
        self.edit_window_regex.setMaximumHeight(60)
        self.edit_window_regex.setPlainText(self.config.window_title_regex)
        window_layout.addWidget(self.edit_window_regex)
        advanced_layout.addWidget(window_group)
        
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
        
        splitter.addWidget(config_widget)
        
        output_group = QGroupBox("📄 Runtime Output & Logs")
        output_layout = QVBoxLayout(output_group)
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 10))
        self.output_area.setPlainText("Ready to start stress testing...\n")
        output_layout.addWidget(self.output_area)
        
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
        
        splitter.setSizes([360, 240])
        main_layout.addWidget(splitter)
        
        button_layout = QHBoxLayout()
        self.btn_save_config = QPushButton("💾 Save Config")
        self.btn_save_config.clicked.connect(self.save_config)
        self.btn_load_config = QPushButton("📂 Load Config")
        self.btn_load_config.clicked.connect(self.load_config)
        self.btn_start = QPushButton("✅ Start Test")
        self.btn_start.clicked.connect(self.start_test)
        
        button_layout.addWidget(self.btn_save_config)
        button_layout.addWidget(self.btn_load_config)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_start)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        self.show_preview()

    def start_test(self):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, "Test Kjører", "En test kjører allerede.")
            return

        self.btn_start.setEnabled(False)
        self.output_area.clear()
        self.append_output("=" * 60 + "\n🚀 Initialiserer stresstest...\n")
        
        config = self.get_current_config()
        
        self.thread = QThread()
        self.worker = StressTestWorker(config)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_test_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.append_output)
        
        self.thread.start()

    def on_test_finished(self):
        result = self.worker.result if self.worker else {}
        success = result.get('success', 0)
        total = result.get('total', self.get_current_config().number_of_messages)
        error = result.get('error')

        summary_message = ""
        if error:
            summary_message = f"Testen ble avsluttet med en kritisk feil:\n{error}"
            QMessageBox.critical(self, "Test Feilet", summary_message)
        else:
            summary_message = f"Stresstesten er ferdig.\n\nResultat: {success} av {total} meldinger ble sendt."
            QMessageBox.information(self, "Test Fullført", summary_message)

        self.append_output("\n" + "=" * 60)
        self.append_output(f"\n🎉 {summary_message}\n")
        self.btn_start.setEnabled(True)

    def append_output(self, text):
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.output_area.ensureCursorVisible()
        # FJERNERT: QApplication.processEvents()
        # Denne linjen ble fjernet for å forhindre at GUI-et fryser
        # ved høyfrekvent signalering fra worker-tråden.

    def clear_output(self):
        self.output_area.clear()

    def save_log(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Log", "stress_test_log.txt", "Text files (*.txt)")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.output_area.toPlainText())

    def get_current_config(self):
        config = Config()
        config.number_of_messages = self.spin_count.value()
        config.wait_time_seconds = self.spin_wait.value()
        config.window_title_regex = self.edit_window_regex.toPlainText().strip()
        config.debug_output_timeout = self.spin_debug_timeout.value()
        config.regenerate_sample_messages()
        return config

    def load_config_to_ui(self, config):
        self.spin_count.setValue(config.number_of_messages)
        self.spin_wait.setValue(config.wait_time_seconds)
        self.edit_window_regex.setPlainText(config.window_title_regex)
        self.spin_debug_timeout.setValue(config.debug_output_timeout)
        self.show_preview()

    def save_config(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Configuration", "config.json", "JSON files (*.json)")
        if filename:
            config = self.get_current_config()
            config.save_to_file(filename)
            QMessageBox.information(self, "Lagret", f"Konfigurasjon lagret til {filename}")

    def load_config(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON files (*.json)")
        if filename:
            try:
                config = Config.load_from_file(filename)
                self.load_config_to_ui(config)
                self.config = config
                QMessageBox.information(self, "Lastet", f"Konfigurasjon lastet fra {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Feil ved lasting", f"Kunne ikke laste konfigurasjon:\n{e}")

    def show_preview(self):
        current_count = self.spin_count.value()
        self.config.number_of_messages = current_count
        self.config.regenerate_sample_messages()
        preview_count = min(5, current_count)
        self.preview.setPlainText("\n".join(self.config.sample_messages[:preview_count]))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Configurator()
    window.show()
    sys.exit(app.exec())

