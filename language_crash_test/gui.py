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
    Main GUI configurator window with thread-safe test execution.
    
    Implements the complete GUI requirements including:
    - Responsive interface with worker threading
    - Configuration management
    - Real-time progress display
    - Timeout protection
    - Graceful error handling
    """

    def __init__(self, parent=None):
        """Initialize the GUI configurator."""
        super().__init__(parent)
        
        # Initialize configuration
        self.config = Config()
        
        # Thread management
        self.thread = None
        self.worker = None
        self.test_timeout_timer = None
        
        # UI setup
        self.setWindowTitle(self.config.gui_window_title)
        self.setMinimumSize(self.config.gui_min_width, self.config.gui_min_height)
        
        # Setup the user interface
        self.setup_ui()
        
        # Load preview
        self.show_preview()

    def setup_ui(self):
        """Set up the user interface components."""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # Configuration panel (left side)
        config_widget = QTabWidget(self)
        
        # Basic configuration tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Basic configuration group
        config_group = QGroupBox("⚙️ Test Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Number of messages
        config_layout.addWidget(QLabel("Number of messages to send:"))
        self.spin_count = QSpinBox(self)
        self.spin_count.setRange(1, 1000)
        self.spin_count.setValue(self.config.number_of_messages)
        self.spin_count.valueChanged.connect(self.show_preview)
        config_layout.addWidget(self.spin_count)
        
        # Wait time between messages
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
        
        # Message preview group
        preview_group = QGroupBox("🧪 Message Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = QTextEdit(self)
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(150)
        preview_layout.addWidget(self.preview)
        basic_layout.addWidget(preview_group)
        
        basic_layout.addStretch()
        config_widget.addTab(basic_tab, "Basic Config")
        
        # Advanced configuration tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Window detection group
        window_group = QGroupBox("🪟 Window Detection")
        window_layout = QVBoxLayout(window_group)
        window_layout.addWidget(QLabel("Window title regex:"))
        self.edit_window_regex = QTextEdit(self)
        self.edit_window_regex.setMaximumHeight(60)
        self.edit_window_regex.setPlainText(self.config.window_title_regex)
        window_layout.addWidget(self.edit_window_regex)
        advanced_layout.addWidget(window_group)
        
        # Debug configuration group
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
        
        # Output panel (right side)
        output_group = QGroupBox("📋 Test Output")
        output_layout = QVBoxLayout(output_group)
        
        # Output text area
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 9))
        output_layout.addWidget(self.output)
        
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
        
        # Set splitter proportions (60% config, 40% output)
        splitter.setSizes([360, 240])
        main_layout.addWidget(splitter)
        
        # Bottom button panel
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
        """Get configuration from current UI state."""
        config = Config()
        config.number_of_messages = self.spin_count.value()
        config.wait_time_seconds = self.spin_wait.value()
        config.language_choice = self.combo_language.currentData()
        config.window_title_regex = self.edit_window_regex.toPlainText().strip()
        config.debug_output_timeout = self.spin_debug_timeout.value()
        config.regenerate_sample_messages()  # Vil nå bruke riktig språk
        return config

    def load_config_to_ui(self, config: Config):
        """Load configuration into UI components."""
        self.spin_count.setValue(config.number_of_messages)
        self.spin_wait.setValue(config.wait_time_seconds)
        
        # Finn indeksen som korresponderer til språkvalget og sett den
        index = self.combo_language.findData(config.language_choice)
        if index != -1:
            self.combo_language.setCurrentIndex(index)
        
        self.edit_window_regex.setPlainText(config.window_title_regex)
        self.spin_debug_timeout.setValue(config.debug_output_timeout)
        self.show_preview()

    def save_config(self):
        """Save current configuration to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "config.json", "JSON files (*.json)"
        )
        if filename:
            try:
                config = self.get_current_config()
                config.save_to_file(filename)
                QMessageBox.information(self, "Saved", f"Configuration saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def load_config(self):
        """Load configuration from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "config.json", "JSON files (*.json)"
        )
        if filename:
            try:
                config = Config.load_from_file(filename)
                self.load_config_to_ui(config)
                QMessageBox.information(self, "Loaded", f"Configuration loaded from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {e}")

    def show_preview(self):
        """Update the message preview."""
        try:
            config = self.get_current_config()
            if config.sample_messages:
                preview_messages = config.sample_messages[:5]  # Show first 5 messages
                preview_text = "\n".join(f"{i+1}. {msg}" for i, msg in enumerate(preview_messages))
                if len(config.sample_messages) > 5:
                    preview_text += f"\n... and {len(config.sample_messages) - 5} more messages"
            else:
                preview_text = "No messages generated"
            
            self.preview.setPlainText(preview_text)
        except Exception as e:
            self.preview.setPlainText(f"Error generating preview: {e}")

    def start_test(self):
        """Start the stress test in a separate thread."""
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, "Test Running", "A test is already running. Please wait for it to complete.")
            return
        
        try:
            # Get current configuration
            self.config = self.get_current_config()
            
            # Validate configuration
            self.config.validate()
            
            # Clear output
            self.clear_output()
            self.append_output("🚀 Starting stress test...")
            
            # Create worker and thread
            self.thread = QThread(self)
            self.worker = StressTestWorker(self.config)
            self.worker.moveToThread(self.thread)
            
            # Set up timeout protection
            estimated_time = (self.config.number_of_messages * self.config.wait_time_seconds + 60) * 1000
            timeout_ms = min(estimated_time, 300000)  # Max 5 minutes
            
            self.test_timeout_timer = QTimer(self)
            self.test_timeout_timer.setSingleShot(True)
            self.test_timeout_timer.timeout.connect(self.on_test_timeout)
            self.test_timeout_timer.start(int(timeout_ms))
            
            # Connect signals
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_test_finished)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.finished.connect(self.test_timeout_timer.stop)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.append_output)
            self.worker.error.connect(self.on_worker_error)
            
            # Update UI state
            self.btn_start.setText("🔄 Running...")
            self.btn_start.setEnabled(False)
            
            # Start the thread
            self.thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start test: {e}")
            self.btn_start.setText("✅ Start Test")
            self.btn_start.setEnabled(True)

    def on_test_timeout(self):
        """Handle test timeout to prevent indefinite hanging."""
        self.append_output("⏰ Test timed out - terminating worker thread...")
        
        if self.worker:
            self.worker.stop()
        
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(5000):  # Wait up to 5 seconds
                self.thread.terminate()
                self.thread.wait()
        
        self.on_test_finished()
        QMessageBox.warning(self, "Timeout", "The test has timed out and was terminated.")

    def on_worker_error(self, error_message: str):
        """Handle errors from worker thread."""
        self.append_output(f"❌ Worker error: {error_message}")

    def on_test_finished(self):
        """Handle test completion."""
        # Reset UI state
        self.btn_start.setText("✅ Start Test")
        self.btn_start.setEnabled(True)
        
        # Clean up timeout timer
        if self.test_timeout_timer:
            self.test_timeout_timer.stop()
            self.test_timeout_timer = None
        
        # Get results if available
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
                self.append_output(f"⚠️ Error getting test results: {e}")
        
        # Clean up worker
        if self.worker:
            self.worker.cleanup()
            self.worker = None
        
        self.thread = None

    def append_output(self, text: str):
        """Append text to output area and scroll to bottom."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        if not text.endswith('\n'):
            cursor.insertText('\n')
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def clear_output(self):
        """Clear the output area."""
        self.output.clear()

    def save_log(self):
        """Save the current output log to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "test_log.txt", "Text files (*.txt)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.output.toPlainText())
                QMessageBox.information(self, "Saved", f"Log saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save log: {e}")

    def closeEvent(self, event):
        """Handle window close event with proper cleanup."""
        if self.thread and self.thread.isRunning():
            reply = QMessageBox.question(
                self, "Test Running", 
                "A test is currently running. Do you want to stop it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Stop the test
                if self.worker:
                    self.worker.stop()
                
                if self.thread:
                    self.thread.quit()
                    if not self.thread.wait(5000):
                        self.thread.terminate()
                
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main function for running the GUI application."""
    if not PYSIDE6_AVAILABLE:
        print("❌ PySide6 not available. Please install with: pip install PySide6")
        return 1
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Language Crash Test")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Language Crash Test Project")
    
    # Create and show main window
    window = Configurator()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

