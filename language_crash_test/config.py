#!/usr/bin/env python3
"""
Configuration Management for Language Crash Test

Provides the Config class that encapsulates all runtime parameters with support
for JSON serialization and deserialization. This eliminates hardcoded values
throughout the codebase.

Architectural Decision Rationale:
- JSON serialization enables easy configuration persistence and sharing
- Centralized config eliminates scattered hardcoded values
- Type hints and validation ensure configuration integrity
- Default values provide sensible fallbacks for all parameters
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from .generator import generate_messages


@dataclass
class Config:
    """
    Configuration class for Language Crash Test application.
    
    All runtime parameters are centralized here to eliminate hardcoded values.
    Supports JSON serialization/deserialization for persistence.
    """
    
    # Core stress test parameters
    number_of_messages: int = 50
    wait_time_seconds: float = 0.5
    
    # UI element detection patterns (Norwegian-friendly)
    window_title_regex: str = r"^Copilot.*"
    
    # Known UI element patterns for fallback discovery
    text_input_patterns: List[str] = None
    send_button_patterns: List[str] = None  
    new_conversation_patterns: List[str] = None
    
    # Control type fallbacks
    text_input_control_types: List[str] = None
    button_control_types: List[str] = None
    
    # Sample messages for testing
    sample_messages: List[str] = None
    
    # Logging configuration
    log_file: str = "session.log"
    log_level: str = "INFO"
    
    # GUI configuration
    gui_window_title: str = "Copilot UI Stress Test Configurator"
    gui_min_width: int = 600
    gui_min_height: int = 500
    
    # Debug configuration
    debug_script_path: str = "copilot_ui_debug.py"
    debug_output_timeout: int = 30

    # Application launch configuration
    copilot_launch_command: str = "explorer.exe ms-copilot://"
    launch_if_not_found: bool = True
    
    def __post_init__(self):
        """Initialize default values for list fields and generate messages."""
        if self.text_input_patterns is None:
            self.text_input_patterns = [
                "InputTextBox",          # Most common technical ID
                "CIB-Compose-Box",       # Another potential technical ID
                "TextBox",
                "MessageInput", 
                "ChatInput"
            ]
        
        if self.send_button_patterns is None:
            self.send_button_patterns = [
                "Snakk med Copilot",     # NORWEGIAN TITLE (Primary)
                "OldComposerMicButton",  # Technical ID
                "SendButton",
                "MicButton"
            ]
        
        if self.new_conversation_patterns is None:
            self.new_conversation_patterns = [
                "Hjem",                  # NORWEGIAN TITLE (Primary, based on log)
                "HomeButton",            # Technical ID
                "Ny samtale",
                "New conversation"
            ]
        
        if self.text_input_control_types is None:
            self.text_input_control_types = ["Edit", "Text", "Document", "Custom"]
        
        if self.button_control_types is None:
            self.button_control_types = ["Button", "Custom", "MenuItem"]
        
        # Generate sample messages only if they haven't been loaded from a file
        if self.sample_messages is None:
            self.regenerate_sample_messages()

    def regenerate_sample_messages(self):
        """
        Generate a new list of sample messages based on number_of_messages.
        This ensures the message list is always in sync with the configuration.
        """
        if self.number_of_messages > 0:
            self.sample_messages = generate_messages(self.number_of_messages)
        else:
            self.sample_messages = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config instance from dictionary (JSON deserialization)."""
        # Get all field names from the class definition
        class_fields = {f.name for f in cls.__dataclass_fields__.values()}
        # Filter the input data to only include keys that are actual fields
        filtered_data = {k: v for k, v in data.items() if k in class_fields}
        return cls(**filtered_data)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            filepath: Path where to save the configuration file
        """
        try:
            config_data = self.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save config to {filepath}: {e}")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Config':
        """
        Load configuration from JSON file.
        
        Args:
            filepath: Path to the configuration file
            
        Returns:
            Config instance loaded from file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            RuntimeError: If config file is invalid
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in config file {filepath}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {filepath}: {e}")
    
    def validate(self) -> bool:
        """
        Validate configuration parameters.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If any configuration parameter is invalid
        """
        if self.number_of_messages <= 0:
            raise ValueError("number_of_messages must be positive")
        
        if self.wait_time_seconds < 0:
            raise ValueError("wait_time_seconds must be non-negative")
        
        if not self.window_title_regex:
            raise ValueError("window_title_regex cannot be empty")
        
        if not self.text_input_patterns:
            raise ValueError("text_input_patterns cannot be empty")
        
        if not self.send_button_patterns:
            raise ValueError("send_button_patterns cannot be empty")
        
        if not self.sample_messages:
            raise ValueError("sample_messages cannot be empty")
        
        return True
    
    def get_runtime_summary(self) -> str:
        """Get a summary string for logging/display purposes."""
        return (
            f"Messages: {self.number_of_messages}, "
            f"Interval: {self.wait_time_seconds}s, "
            f"Sample messages: {len(self.sample_messages)}"
        )


def create_default_config_file(filepath: str = "config.json") -> Config:
    """
    Create a default configuration file if it doesn't exist.
    
    Args:
        filepath: Path where to create the default config file
        
    Returns:
        Config instance that was created
    """
    if not os.path.exists(filepath):
        config = Config()
        config.save_to_file(filepath)
        return config
    else:
        return Config.load_from_file(filepath)


if __name__ == "__main__":
    # Demo/test the configuration system
    print("Testing Configuration System")
    print("=" * 40)
    
    # Create default config
    config = Config()
    print(f"Default config: {config.get_runtime_summary()}")
    
    # Test serialization
    config.save_to_file("test_config.json")
    print("✅ Saved config to test_config.json")
    
    # Test deserialization
    loaded_config = Config.load_from_file("test_config.json")
    print(f"Loaded config: {loaded_config.get_runtime_summary()}")
    
    # Test validation
    try:
        loaded_config.validate()
        print("✅ Configuration validation passed")
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
    
    # Cleanup
    os.remove("test_config.json")
    print("🧹 Cleaned up test file")

