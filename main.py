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

# Import package modules
from language_crash_test import Config, run_stress_test_logic, inspect_ui_elements, GUI_AVAILABLE

# GUI imports (conditional)
Configurator = None
if GUI_AVAILABLE:
    try:
        from language_crash_test import Configurator
    except ImportError:
        GUI_AVAILABLE = False


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
    
    try:
        result = run_stress_test_logic(config, logger)
        success_count = result.get('success', 0)
        total_messages = result.get('total', 0)
        error = result.get('error')

        print("="*60)
        if error:
            print(f"❌ Test failed: {error}")
            sys.exit(1)

        print("🎉 Stress test completed!")
        print(f"📊 Total sent: {success_count} of {total_messages} messages")

        if success_count == 0:
            print("❌ No messages sent - exiting with error")
            sys.exit(1)
        elif success_count < total_messages:
            print(f"⚠️ {total_messages - success_count} messages failed - partial success")
            sys.exit(0)
        else:
            print("✅ All messages sent successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        sys.exit(1)


def run_gui_configurator():
    """Launch the GUI configurator."""
    # Use the global GUI_AVAILABLE that was set at import time
    import language_crash_test
    if not language_crash_test.GUI_AVAILABLE:
        print("❌ GUI dependencies not available. Install with: pip install PySide6")
        sys.exit(1)
    
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = Configurator()
        window.show()
        return app.exec()
    except ImportError:
        print("❌ PySide6 not available. Install with: pip install PySide6")
        sys.exit(1)


def run_debug_mode(config):
    """Run debug mode to inspect UI elements."""
    print("🔍 Running debug mode to inspect UI elements...")
    print(f"Looking for window matching: {config.window_title_regex}")
    
    try:
        # Use the debug module from our package
        result = inspect_ui_elements(config.window_title_regex)
        
        if result:
            print("\n✅ UI inspection completed successfully")
            print(f"Found {result['analysis_summary']['text_inputs_found']} text input candidates")
            print(f"Found {result['analysis_summary']['send_buttons_found']} send button candidates") 
            print(f"Found {result['analysis_summary']['new_conversation_buttons_found']} new conversation candidates")
        else:
            print("❌ UI inspection failed - could not connect to window")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Debug mode failed: {e}")
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
        # Load config for debug mode
        try:
            if Path(args.config).exists():
                config = Config.load_from_file(args.config)
            else:
                config = Config()  # Use defaults
            run_debug_mode(config)
        except Exception as e:
            print(f"❌ Could not load config for debug: {e}")
            sys.exit(1)
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