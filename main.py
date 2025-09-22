#!/usr/bin/env python3
"""
Language Crash Test - Unified Entry Point

Main entry point for the Microsoft Copilot UI stress testing application.
Provides options to run the stress test, configure settings via GUI, or run debug mode.

Usage:
    python main.py                 # Run stress test with default/config settings
    python main.py --gui           # Open GUI configurator
    python main.py --debug         # Run debug mode to inspect UI elements
    python main.py --config FILE   # Use specific config file
"""

import sys
import argparse
import logging
from pathlib import Path

# Import modules
from config import Config
import copilot_ui_stress_test
import copilot_ui_debug

# GUI imports (optional dependency)
GUI_AVAILABLE = False
try:
    import gui_configurator
    GUI_AVAILABLE = True
except ImportError:
    # GUI dependencies not available
    pass


def setup_logging(config):
    """Setup logging to both file and console based on config."""
    # Create session.log (overwrite each run)
    log_file = Path("session.log")
    if log_file.exists():
        log_file.unlink()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('session.log', mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=== Language Crash Test Session Started ===")
    logger.info(f"Configuration: {config.number_of_messages} messages, {config.wait_time_seconds}s interval")
    return logger


def run_stress_test(config):
    """Run the main stress test with given configuration."""
    logger = setup_logging(config)
    logger.info("Starting Microsoft Copilot UI Stress Test")
    
    # Set global config for the stress test module
    copilot_ui_stress_test.set_config(config)
    
    try:
        copilot_ui_stress_test.main()
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        sys.exit(1)


def run_gui_configurator():
    """Launch the GUI configurator."""
    if not GUI_AVAILABLE:
        print("❌ GUI dependencies not available. Install with: pip install PySide6")
        sys.exit(1)
    
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = gui_configurator.Configurator()
        window.show()
        return app.exec()
    except ImportError:
        print("❌ PySide6 not available. Install with: pip install PySide6")
        sys.exit(1)


def run_debug_mode():
    """Run debug mode to inspect UI elements."""
    logger = setup_logging(Config())  # Use default config for debug
    logger.info("Starting debug mode")
    
    try:
        copilot_ui_debug.main()
    except Exception as e:
        logger.error(f"Debug mode failed: {e}")
        sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Language Crash Test - Microsoft Copilot UI Stress Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run stress test with default settings
  python main.py --gui              # Open GUI configurator  
  python main.py --debug            # Inspect UI elements
  python main.py --config my.json   # Use custom config file
        """
    )
    
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="Launch GUI configurator"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Run in debug mode to inspect UI elements"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.gui:
        sys.exit(run_gui_configurator())
    elif args.debug:
        run_debug_mode()
    else:
        # Load configuration
        try:
            config = Config.load_from_file(args.config)
        except FileNotFoundError:
            print(f"Config file {args.config} not found. Creating default configuration.")
            config = Config()
            config.save_to_file(args.config)
            print(f"Default configuration saved to {args.config}")
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration.")
            config = Config()
        
        run_stress_test(config)


if __name__ == "__main__":
    main()