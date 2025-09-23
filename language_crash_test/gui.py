#!/usr/bin/env python3
"""
GUI Module for Language Crash Test

Main GUI window using PySide6 with responsive threading for stress test execution.
Implements the requirements from the new instruction for proper thread-safe operation.

Key Features:
- PySide6-based responsive GUI that never freezes
- Proper QThread and QObject worker pattern implementation
- Signal throttling to prevent GUI overload
- Thread-safe communication via Qt signals/slots
- Timeout protection and graceful shutdown
- Configuration management with save/load functionality
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QSpinBox, QPushButton, QTextEdit, QFileDialog, QMessageBox, QSplitter,
        QDoubleSpinBox, QTabWidget, QGroupBox, QComboBox
    )
    from PySide6.QtCore import Qt, QThread, QTimer
    from PySide6.QtGui import QTextCursor, QFont
    PYSIDE6_AVAILABLE = True
except ImportError as e:
    # PySide6 not available - create stubs for testing
    PYSIDE6_AVAILABLE = False
    print(f"PySide6 import error: {e}")
    
    class QWidget:
        def __init__(self): pass
    
    class QApplication:
        def __init__(self, args): pass
        def exec(self): return 0
    
    # ... other stubs would go here

# Import our package modules
from .config import Config
from .worker import StressTestWorker


class Configurator(QWidget):
    """
    Hovedvindu for GUI-konfigurasjon med trådsikker testkjøring.
    
    Implementerer alle GUI-krav, inkludert:
    - Responsivt grensesnitt med worker-tråder
    - Konfigurasjonshåndtering
    - Sanntidsvisning av fremdrift
    - Tidsavbruddsbeskyttelse
    - Robust feilhåndtering
    """

    def __init__(self, parent=None):
        """Initialiserer GUI-konfiguratoren."""
        super().__init__(parent)
        
        # Initialiserer konfigurasjonen
        self.config = Config()
        self.logger = logging.getLogger(__name__) # Logger for GUI-hendelser
        
        # Trådhåndtering
        self.thread = None
        self.worker = None
        self.test_timeout_timer = None
        
        # UI-oppsett
        self.setWindowTitle(self.config.gui_window_title)
        self.setMinimumSize(self.config.gui_min_width, self.config.gui_min_height)
        
        # Setter opp brukergrensesnittet
        self.setup_ui()
        
        # Laster forhåndsvisning
        self.show_preview()

    def setup_ui(self):
        """Setter opp brukergrensesnittkomponentene."""
        main_layout = QVBoxLayout(self)
        
        # Oppretter en splitter for et justerbart layout
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # Konfigurasjonspanel (venstre side)
        config_widget = QTabWidget(self)
        
        # Fane for grunnleggende konfigurasjon
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Gruppe for testkonfigurasjon
        config_group = QGroupBox("⚙️ Test Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Antall meldinger
        config_layout.addWidget(QLabel("Number of messages to send:"))
        self.spin_count = QSpinBox(self)
        self.spin_count.setRange(1, 1000)
        self.spin_count.setValue(self.config.number_of_messages)
        self.spin_count.valueChanged.connect(self.show_preview)
        config_layout.addWidget(self.spin_count)
        
        # Ventetid mellom meldinger
        config_layout.addWidget(QLabel("Wait time between messages (seconds):"))
        self.spin_wait = QDoubleSpinBox(self)
        self.spin_wait.setRange(0.1, 10.0)
        self.spin_wait.setSingleStep(0.1)
        self.spin_wait.setValue(self.config.wait_time_seconds)
        config_layout.addWidget(self.spin_wait)
        
        # Språkvalg
        config_layout.addWidget(QLabel("Språk for meldinger:"))
        self.combo_language = QComboBox(self)
        self.combo_language.addItem("Norsk og Engelsk (Blandet)", "both")
        self.combo_language.addItem("Kun Norsk", "norwegian")
        self.combo_language.addItem("Kun Engelsk", "english")
        self.combo_language.currentIndexChanged.connect(self.show_preview)
        config_layout.addWidget(self.combo_language)
        
        basic_layout.addWidget(config_group)
        
        # Gruppe for forhåndsvisning av meldinger
        preview_group = QGroupBox("🧪 Message Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = QTextEdit(self)
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(150)
        preview_layout.addWidget(self.preview)
        basic_layout.addWidget(preview_group)
        
        basic_layout.addStretch()
        config_widget.addTab(basic_tab, "Basic Config")
        
        # Fane for avansert konfigurasjon
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Gruppe for vindusgjenkjenning
        window_group = QGroupBox("🪟 Window Detection")
        window_layout = QVBoxLayout(window_group)
        window_layout.addWidget(QLabel("Window title regex:"))
        self.edit_window_regex = QTextEdit(self)
        self.edit_window_regex.setMaximumHeight(60)
        self.edit_window_regex.setPlainText(self.config.window_title_regex)
        window_layout.addWidget(self.edit_window_regex)
        advanced_layout.addWidget(window_group)
        
        # Gruppe for feilsøkingsinnstillinger
        debug_group = QGroupBox("🔧 Debug Settings")
        debug_layout = QVBoxLayout(debug_group)
        debug_layout.addWidget(QLabel("Debug output timeout (seconds):"))
        self.spin_debug_timeout = QSpinBox(self)
        self.spin_debug_timeout.setRange(10, 120)
        self.spin_debug_timeout.setValue(self.config.debug_output_timeout)
        debug_layout.addWidget(self.spin_debug_timeout)
        advanced_layout.addWidget(debug_group)
        
        advanced_layout.addStretch()
        config_widget.addTab(advanced_tab, "Advanced")
        
        splitter.addWidget(config_widget)
        
        # Output-panel (høyre side)
        output_group = QGroupBox("📋 Test Output")
        output_layout = QVBoxLayout(output_group)
        
        # Tekstområde for output
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 9))
        output_layout.addWidget(self.output)
        
        # Kontroller for output
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
        
        # Setter størrelsesforhold for splitter (60% config, 40% output)
        splitter.setSizes([360, 240])
        main_layout.addWidget(splitter)
        
        # Knappepanel nederst
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

    def get_current_config(self) -> Config:
        """Henter konfigurasjon fra gjeldende UI-tilstand."""
        self.logger.info("Henter gjeldende konfigurasjon fra UI.")
        config = Config()
        config.number_of_messages = self.spin_count.value()
        config.wait_time_seconds = self.spin_wait.value()
        config.language_choice = self.combo_language.currentData()
        config.window_title_regex = self.edit_window_regex.toPlainText().strip()
        config.debug_output_timeout = self.spin_debug_timeout.value()
        config.regenerate_sample_messages() # Vil nå bruke riktig språk
        return config

    def load_config_to_ui(self, config: Config):
        """Laster konfigurasjon inn i UI-komponenter."""
        self.logger.info("Laster konfigurasjon til UI.")
        self.spin_count.setValue(config.number_of_messages)
        self.spin_wait.setValue(config.wait_time_seconds)
        
        # Finner indeksen som korresponderer til språkvalget og setter den
        index = self.combo_language.findData(config.language_choice)
        if index != -1:
            self.combo_language.setCurrentIndex(index)
        
        self.edit_window_regex.setPlainText(config.window_title_regex)
        self.spin_debug_timeout.setValue(config.debug_output_timeout)
        self.show_preview()

    def save_config(self):
        """Lagrer gjeldende konfigurasjon til fil."""
        self.logger.info("Lagre konfigurasjon-knapp trykket.")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "config.json", "JSON files (*.json)"
        )
        if filename:
            try:
                config_to_save = self.get_current_config()
                config_to_save.save_to_file(filename)
                self.logger.info(f"Konfigurasjon lagret til {filename}")
                QMessageBox.information(self, "Saved", f"Configuration saved to {filename}")
            except Exception as e:
                self.logger.error(f"Klarte ikke å lagre konfigurasjon: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def load_config(self):
        """Laster konfigurasjon fra fil."""
        self.logger.info("Last inn konfigurasjon-knapp trykket.")
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "config.json", "JSON files (*.json)"
        )
        if filename:
            try:
                self.config = Config.load_from_file(filename)
                self.load_config_to_ui(self.config)
                self.logger.info(f"Konfigurasjon lastet fra {filename}")
                QMessageBox.information(self, "Loaded", f"Configuration loaded from {filename}")
            except Exception as e:
                self.logger.error(f"Klarte ikke å laste konfigurasjon: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {e}")

    def show_preview(self):
        """Oppdaterer forhåndsvisningen av meldinger."""
        try:
            config = self.get_current_config()
            if config.sample_messages:
                preview_messages = config.sample_messages[:5]  # Viser de første 5 meldingene
                preview_text = "\n".join(f"{i+1}. {msg}" for i, msg in enumerate(preview_messages))
                if len(config.sample_messages) > 5:
                    preview_text += f"\n... and {len(config.sample_messages) - 5} more messages"
            else:
                preview_text = "No messages generated"
            
            self.preview.setPlainText(preview_text)
        except Exception as e:
            self.logger.warning(f"Feil ved generering av forhåndsvisning: {e}")
            self.preview.setPlainText(f"Error generating preview: {e}")

    def start_test(self):
        """Starter stresstesten i en separat tråd."""
        if self.thread and self.thread.isRunning():
            self.logger.warning("Forsøkte å starte en test mens en annen kjører.")
            QMessageBox.warning(self, "Test Running", "A test is already running. Please wait for it to complete.")
            return
        
        try:
            # Henter gjeldende konfigurasjon
            self.config = self.get_current_config()
            
            # Validerer konfigurasjonen
            self.config.validate()
            
            # Tømmer output
            self.clear_output()
            self.append_output("🚀 Starting stress test...")
            self.logger.info("Starter stresstest...")
            
            # Oppretter worker og tråd
            self.thread = QThread(self)
            self.worker = StressTestWorker(self.config)
            self.worker.moveToThread(self.thread)
            
            # Setter opp tidsavbruddsbeskyttelse
            estimated_time = (self.config.number_of_messages * self.config.wait_time_seconds + 60) * 1000
            timeout_ms = min(estimated_time, 300000)  # Maks 5 minutter
            
            self.test_timeout_timer = QTimer(self)
            self.test_timeout_timer.setSingleShot(True)
            self.test_timeout_timer.timeout.connect(self.on_test_timeout)
            self.test_timeout_timer.start(int(timeout_ms))
            
            # Kobler signaler
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_test_finished)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.finished.connect(self.test_timeout_timer.stop)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.append_output)
            self.worker.error.connect(self.on_worker_error)
            
            # Oppdaterer UI-tilstand
            self.btn_start.setText("🔄 Running...")
            self.btn_start.setEnabled(False)
            
            # Starter tråden
            self.thread.start()
            
        except Exception as e:
            self.logger.error(f"Klarte ikke å starte testen: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to start test: {e}")
            self.btn_start.setText("✅ Start Test")
            self.btn_start.setEnabled(True)

    def on_test_timeout(self):
        """Håndterer tidsavbrudd for å forhindre at applikasjonen henger."""
        self.logger.warning("Testen timet ut, avslutter worker-tråden.")
        self.append_output("⏰ Test timed out - terminating worker thread...")
        
        if self.worker:
            self.worker.stop()
        
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(5000):  # Venter opptil 5 sekunder
                self.thread.terminate()
                self.thread.wait()
        
        self.on_test_finished()
        QMessageBox.warning(self, "Timeout", "The test has timed out and was terminated.")

    def on_worker_error(self, error_message: str):
        """Håndterer feil fra worker-tråden."""
        self.logger.error(f"Feil i worker: {error_message}")
        self.append_output(f"❌ Worker error: {error_message}")

    def on_test_finished(self):
        """Håndterer fullføring av testen."""
        self.logger.info("Testen er ferdig.")
        # Tilbakestiller UI-tilstand
        self.btn_start.setText("✅ Start Test")
        self.btn_start.setEnabled(True)
        
        # Rengjør tidsavbruddstimer
        if self.test_timeout_timer:
            self.test_timeout_timer.stop()
            self.test_timeout_timer = None
        
        # Henter resultater hvis tilgjengelig
        if self.worker:
            try:
                result = self.worker.get_result()
                success_count = result.get('success', 0)
                total_messages = result.get('total', 0)
                error_msg = result.get('error')
                
                if error_msg:
                    self.append_output(f"❌ Test failed: {error_msg}")
                    QMessageBox.critical(self, "Test Failed", f"The test failed with error: {error_msg}")
                else:
                    self.append_output(f"✅ Test completed: {success_count}/{total_messages} messages sent")
                    if success_count == total_messages:
                        QMessageBox.information(self, "Test Completed", f"Test completed successfully! Sent {success_count} messages.")
                    else:
                        QMessageBox.warning(self, "Test Completed", f"Test completed with issues. Sent {success_count}/{total_messages} messages.")
                
            except Exception as e:
                self.logger.warning(f"Feil ved henting av testresultater: {e}")
                self.append_output(f"⚠️ Error getting test results: {e}")
        
        # Rengjør worker
        if self.worker:
            self.worker.cleanup()
            self.worker = None
        
        self.thread = None

    def append_output(self, text: str):
        """Legger til tekst i output-området og ruller til bunnen."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        if not text.endswith('\n'):
            cursor.insertText('\n')
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def clear_output(self):
        """Tømmer output-området."""
        self.logger.info("Tømmer output-loggen.")
        self.output.clear()

    def save_log(self):
        """Lagrer gjeldende output-logg til en fil."""
        self.logger.info("Lagre logg-knapp trykket.")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "test_log.txt", "Text files (*.txt)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.output.toPlainText())
                self.logger.info(f"Logg lagret til {filename}")
                QMessageBox.information(self, "Saved", f"Log saved to {filename}")
            except Exception as e:
                self.logger.error(f"Klarte ikke å lagre loggen: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to save log: {e}")

    def closeEvent(self, event):
        """Håndterer lukking av vinduet med korrekt opprydding."""
        if self.thread and self.thread.isRunning():
            self.logger.info("Avslutningsforespørsel mens testen kjører.")
            reply = QMessageBox.question(
                self, "Test Running", 
                "A test is currently running. Do you want to stop it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("Brukeren valgte å stoppe testen og avslutte.")
                # Stopper testen
                if self.worker:
                    self.worker.stop()
                
                if self.thread:
                    self.thread.quit()
                    if not self.thread.wait(5000):
                        self.thread.terminate()
                
                event.accept()
            else:
                self.logger.info("Brukeren valgte å ikke avslutte.")
                event.ignore()
        else:
            event.accept()


def main():
    """Hovedfunksjon for å kjøre GUI-applikasjonen."""
    if not PYSIDE6_AVAILABLE:
        print("❌ PySide6 not available. Please install with: pip install PySide6")
        return 1
    
    app = QApplication(sys.argv)
    
    # Setter applikasjonsegenskaper
    app.setApplicationName("Language Crash Test")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Language Crash Test Project")
    
    # Oppretter og viser hovedvinduet
    window = Configurator()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    # Setter opp grunnleggende logging for GUI-modulen
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sys.exit(main())
