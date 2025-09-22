#!/usr/bin/env python3
"""
Language Crash Test Package

A robust Python application package for stress-testing Microsoft Copilot for Windows UI 
by automating bilingual conversations. Provides both CLI and GUI interfaces with 
responsive threading for optimal user experience.

Main Components:
- automation: Core pywinauto UI automation logic
- config: Configuration management with JSON persistence 
- debug: UI element inspection utilities
- generator: Bilingual message generation (English/Norwegian)
- gui: PySide6 GUI main window
- worker: QObject worker for thread-safe GUI operations

Usage:
    from language_crash_test import Config, run_stress_test_logic
    from language_crash_test.gui import Configurator
    from language_crash_test.debug import inspect_ui_elements
"""

__version__ = "2.0.0"
__author__ = "Language Crash Test Project"
__description__ = "Microsoft Copilot UI Stress Testing Application"

# Import main components for easy access
from .config import Config, create_default_config_file
from .generator import generate_messages
from .automation import run_stress_test_logic
from .debug import inspect_ui_elements, print_control_identifiers

# GUI components (optional import)
GUI_AVAILABLE = False
Configurator = None
StressTestWorker = None

try:
    from .gui import Configurator
    from .worker import StressTestWorker
    GUI_AVAILABLE = True
except ImportError:
    # PySide6 not available - this is fine, just means no GUI
    pass

__all__ = [
    'Config',
    'create_default_config_file',
    'generate_messages', 
    'run_stress_test_logic',
    'inspect_ui_elements',
    'print_control_identifiers',
    'Configurator',
    'StressTestWorker',
    'GUI_AVAILABLE'
]