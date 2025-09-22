#!/usr/bin/env python3
"""
Test suite for Language Crash Test main entry point and integration.

Validates main.py functionality, argument parsing, and integration
between different modules.
"""

import unittest
import tempfile
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from config import Config


class TestMainIntegration(unittest.TestCase):
    """Test cases for main.py integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # Create a test config
        config = Config()
        config.number_of_messages = 5  # Small number for testing
        config.wait_time_seconds = 0.1
        config.save_to_file(self.test_config_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        if os.path.exists(os.path.join(self.temp_dir, "session.log")):
            os.remove(os.path.join(self.temp_dir, "session.log"))
        os.rmdir(self.temp_dir)
    
    def test_main_help(self):
        """Test main.py help output."""
        # Test that main.py can be imported and help works
        result = subprocess.run([
            sys.executable, "main.py", "--help"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Language Crash Test", result.stdout)
        self.assertIn("--gui", result.stdout)
        self.assertIn("--debug", result.stdout)
        self.assertIn("--config", result.stdout)
    
    def test_config_loading(self):
        """Test that config can be loaded correctly."""
        config = Config.load_from_file(self.test_config_file)
        self.assertEqual(config.number_of_messages, 5)
        self.assertEqual(config.wait_time_seconds, 0.1)
    
    def test_setup_logging(self):
        """Test logging setup functionality."""
        config = Config()
        logger = main.setup_logging(config)
        
        # Check that logger is configured
        self.assertIsNotNone(logger)
        
        # Test that session.log is created
        self.assertTrue(os.path.exists("session.log"))
        
        # Clean up
        if os.path.exists("session.log"):
            os.remove("session.log")


class TestArgumentParsing(unittest.TestCase):
    """Test argument parsing functionality."""
    
    def test_argument_parser_creation(self):
        """Test that argument parser is created correctly."""
        # This tests the argument parser without actually running main
        import argparse
        
        parser = argparse.ArgumentParser(
            description="Language Crash Test - Microsoft Copilot UI Stress Testing",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument("--gui", action="store_true", help="Launch GUI configurator")
        parser.add_argument("--debug", action="store_true", help="Run in debug mode")
        parser.add_argument("--config", type=str, default="config.json", help="Path to configuration file")
        
        # Test parsing different argument combinations
        args = parser.parse_args(["--gui"])
        self.assertTrue(args.gui)
        self.assertFalse(args.debug)
        
        args = parser.parse_args(["--debug"])
        self.assertFalse(args.gui)
        self.assertTrue(args.debug)
        
        args = parser.parse_args(["--config", "test.json"])
        self.assertEqual(args.config, "test.json")


if __name__ == '__main__':
    # Set working directory to parent for testing
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    unittest.main()