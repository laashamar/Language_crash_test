from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QSpinBox, QPushButton, QTextEdit, QFileDialog, QMessageBox, QSplitter,
    QDoubleSpinBox, QTabWidget, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QFont
import sys
import logging
from io import StringIO
from pathlib import Path
from generator import generate_messages
from config import Config


class Configurator(QWidget):
    """Enhanced GUI configurator with scrollable output field and config integration."""
    
    def __init__(self):
        super().__init__()
        self.config = Config()  # Load default config
        self.setWindowTitle("Copilot UI Stress Test Configurator")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the enhanced UI with scrollable output field."""
        main_layout = QVBoxLayout()
        
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

    def append_output(self, text):
        """Append text to the output area."""
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()

    def clear_output(self):
        """Clear the output area."""
        self.output_area.clear()
        self.append_output("Output cleared.\n")

    def save_log(self):
        """Save the current output to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "stress_test_log.txt", "Text files (*.txt)"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.output_area.toPlainText())
            self.append_output(f"Log saved to {filename}\n")

    def get_current_config(self):
        """Get current configuration from UI."""
        config = Config()
        config.number_of_messages = self.spin_count.value()
        config.wait_time_seconds = self.spin_wait.value()
        config.window_title_regex = self.edit_window_regex.toPlainText().strip()
        return config

    def load_config_to_ui(self, config):
        """Load configuration into UI."""
        self.spin_count.setValue(config.number_of_messages)
        self.spin_wait.setValue(config.wait_time_seconds)
        self.edit_window_regex.setPlainText(config.window_title_regex)

    def save_config(self):
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

    def load_config(self):
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

    def get_language_mode(self):
        """Get selected language mode."""
        if self.radio_os.isChecked():
            return "os"
        elif self.radio_eng.isChecked():
            return "english"
        else:
            return "both"

    def show_preview(self):
        """Show preview of generated messages."""
        try:
            count = min(5, self.spin_count.value())
            messages = generate_messages(count)
            self.preview.setPlainText("\n".join(messages))
            self.append_output(f"Generated preview with {count} messages\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate preview: {e}")

    def start_test(self):
        """Start the stress test with current configuration."""
        try:
            self.append_output("=" * 50 + "\n")
            self.append_output("Starting Copilot UI Stress Test...\n")
            
            # Get current config
            config = self.get_current_config()
            lang_mode = self.get_language_mode()
            
            self.append_output(f"Configuration: {config.get_runtime_summary()}\n")
            self.append_output(f"Language mode: {lang_mode}\n")
            
            # Save current config
            config.save_to_file("current_session_config.json")
            
            # Here you would integrate with the actual stress test
            # For now, we'll just simulate it
            self.append_output("Test configuration saved.\n")
            self.append_output("To run the actual test, use: python main.py --config current_session_config.json\n")
            
            QMessageBox.information(
                self, 
                "Test Ready", 
                f"Test configured with {config.number_of_messages} messages.\n"
                f"Configuration saved to current_session_config.json\n\n"
                f"To run the test, execute:\n"
                f"python main.py --config current_session_config.json"
            )
            
        except Exception as e:
            self.append_output(f"Error starting test: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed to start test: {e}")

    def export_messages(self):
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