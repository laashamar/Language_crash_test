#!/usr/bin/env python3
"""
Test suite for Language Crash Test configuration system.

Validates core functionality including config loading, serialization,
and validation logic.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
import sys

# Import from the new package structure
from language_crash_test.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        os.rmdir(self.temp_dir)
    
    def test_default_config_creation(self):
        """Test that default configuration is created correctly."""
        config = Config()
        
        # Test default values
        self.assertEqual(config.number_of_messages, 50)
        self.assertEqual(config.wait_time_seconds, 0.5)
        self.assertEqual(config.language_choice, "both")
        self.assertEqual(config.window_title_regex, r"^Copilot.*")
        
        # Test that patterns are populated
        self.assertIsInstance(config.text_input_patterns, list)
        self.assertGreater(len(config.text_input_patterns), 0)
        self.assertIsInstance(config.send_button_patterns, list)
        self.assertGreater(len(config.send_button_patterns), 0)
        
        # Test that sample messages are generated
        self.assertIsInstance(config.sample_messages, list)
        self.assertEqual(len(config.sample_messages), 50)
    
    def test_config_serialization(self):
        """Test config serialization to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['number_of_messages'], 50)
        self.assertEqual(config_dict['language_choice'], 'both')
        self.assertEqual(config_dict['wait_time_seconds'], 0.5)
    
    def test_config_deserialization(self):
        """Test config deserialization from dictionary."""
        test_data = {
            'number_of_messages': 100,
            'wait_time_seconds': 1.0,
            'language_choice': 'norwegian',
            'window_title_regex': r'^Test.*'
        }
        
        config = Config.from_dict(test_data)
        self.assertEqual(config.number_of_messages, 100)
        self.assertEqual(config.wait_time_seconds, 1.0)
        self.assertEqual(config.language_choice, 'norwegian')
        self.assertEqual(config.window_title_regex, r'^Test.*')
    
    def test_config_file_save_load(self):
        """Test saving and loading config from file."""
        # Create and customize config
        config = Config()
        config.number_of_messages = 25
        config.wait_time_seconds = 0.8
        config.language_choice = "english"
        
        # Save to file
        config.save_to_file(self.test_config_file)
        self.assertTrue(os.path.exists(self.test_config_file))
        
        # Load from file
        loaded_config = Config.load_from_file(self.test_config_file)
        self.assertEqual(loaded_config.number_of_messages, 25)
        self.assertEqual(loaded_config.wait_time_seconds, 0.8)
        self.assertEqual(loaded_config.language_choice, "english")
    
    def test_config_validation(self):
        """Test config validation."""
        config = Config()
        
        # Valid config should pass
        self.assertTrue(config.validate())
        
        # Invalid number of messages
        config.number_of_messages = 0
        with self.assertRaises(ValueError):
            config.validate()
        
        # Reset and test negative wait time
        config.number_of_messages = 50
        config.wait_time_seconds = -1
        with self.assertRaises(ValueError):
            config.validate()
        
        # Reset and test empty regex
        config.wait_time_seconds = 0.5
        config.window_title_regex = ""
        with self.assertRaises(ValueError):
            config.validate()

        # Reset and test invalid language choice
        config.window_title_regex = r"^Copilot.*"
        config.language_choice = "french"
        with self.assertRaises(ValueError):
            config.validate()
    
    def test_config_file_not_found(self):
        """Test loading from non-existent file."""
        with self.assertRaises(FileNotFoundError):
            Config.load_from_file("non_existent_file.json")
    
    def test_config_invalid_json(self):
        """Test loading from invalid JSON file."""
        # Create invalid JSON file
        with open(self.test_config_file, 'w') as f:
            f.write("invalid json content")
        
        with self.assertRaises(RuntimeError):
            Config.load_from_file(self.test_config_file)
    
    def test_get_runtime_summary(self):
        """Test runtime summary generation."""
        config = Config()
        summary = config.get_runtime_summary()
        
        self.assertIsInstance(summary, str)
        self.assertIn("Messages:", summary)
        self.assertIn("Interval:", summary)
        self.assertIn("Language:", summary)
        self.assertIn("Sample messages:", summary)


if __name__ == '__main__':
    unittest.main()
