# Language Crash Test
Stress-testing Copilot UI via bilingual automation script with unified configuration management

## Overview

This repository contains Python scripts for automated stress testing of the Microsoft Copilot desktop application. The scripts simulate realistic user interactions by sending bilingual messages (English and Norwegian) with emojis and special characters to test the application's performance and stability.

## Features

- **Unified Entry Point**: Single `main.py` with GUI, debug, and CLI modes
- **Configuration Management**: JSON-based config system with serialization/deserialization
- **Bilingual Testing**: Messages in both English and Norwegian with special characters (æ, ø, å)
- **Enhanced GUI**: Tabbed interface with scrollable output and real-time logging
- **Optimized UI Detection**: Combined criteria searches instead of sequential checking
- **Comprehensive Logging**: Dual output to console and session.log with timestamp synchronization
- **Robust Error Handling**: Graceful handling of all UI automation exceptions
- **Test Suite**: 18 automated tests validating core functionality
- **CI/CD Pipeline**: Automated testing and validation via GitHub Actions

## Architecture

### Configuration System
The application uses a centralized configuration system with these architectural decisions:

- **JSON Serialization**: Enables easy configuration persistence and sharing between GUI and CLI
- **Centralized Config**: Eliminates scattered hardcoded values throughout the codebase
- **Type Validation**: Ensures configuration integrity with runtime validation
- **Default Fallbacks**: Provides sensible defaults for all parameters

### UI Automation Optimization
The UI element detection system has been optimized:

- **Combined Criteria**: Single `window.child_window(auto_id=X, control_type=Y)` calls instead of sequential checking
- **Efficient Fallbacks**: Prioritized search with automatic fallback to individual criteria
- **Dynamic Discovery**: Integration with debug script for real-time element detection

### Logging Strategy
Dual logging approach for comprehensive monitoring:

- **File Logging**: `session.log` regenerated on each run to avoid stale state
- **GUI Integration**: Real-time output display synchronized with file logging
- **Structured Format**: Timestamped entries with appropriate log levels

## Requirements

- Windows operating system
- Microsoft Copilot for Windows application
- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python .test/run_tests.py
```

## Usage

### Unified Entry Point

The application now provides a single entry point with multiple modes:

```bash
# Run stress test with default settings
python main.py

# Open GUI configurator
python main.py --gui

# Run debug mode to inspect UI elements  
python main.py --debug

# Use custom configuration file
python main.py --config my_config.json
```

### GUI Mode

Launch the enhanced GUI configurator:

```bash
python main.py --gui
```

Features:
- Tabbed configuration interface (Basic/Advanced)
- Real-time message preview
- Scrollable output area with runtime logs
- Configuration save/load functionality
- Message export capabilities

### Configuration Management

The system automatically creates and manages configuration files:

```bash
# Creates default config.json if not found
python main.py

# Save/load custom configurations via GUI
python main.py --gui

# Use specific config file
python main.py --config production.json
```

### Legacy Usage (Still Supported)

```bash
# Direct script execution (uses default config)
python copilot_ui_stress_test.py

# Debug mode
python copilot_ui_debug.py
```

### CI/CD Integration

The repository includes a GitHub Actions workflow that:

1. **Validates syntax** on all platforms
2. **Tests Windows compatibility** when Copilot is available
3. **Runs code quality checks** with linting tools
4. **Generates test reports** as artifacts

#### Manual Workflow Trigger

You can manually trigger the stress test workflow with custom parameters:

1. Go to the "Actions" tab in the GitHub repository
2. Select "Copilot UI Stress Test" workflow
3. Click "Run workflow"
4. Configure parameters:
   - Number of messages (configurable via config file)
   - Wait time between messages (configurable via config file)

#### Automatic Triggers

- **Push to main/develop**: Runs syntax and quality checks
- **Pull requests**: Full validation suite
- **Commit messages with `[run-stress-test]`**: Triggers Windows stress test

## Configuration

The application uses a comprehensive configuration system stored in JSON format:

### Default Configuration

```json
{
    "number_of_messages": 50,
    "wait_time_seconds": 0.5,
    "window_title_regex": "^Copilot.*",
    "text_input_patterns": ["InputTextBox", "CIB-Compose-Box", "TextBox"],
    "send_button_patterns": ["Snakk med Copilot", "OldComposerMicButton"],
    "sample_messages": ["Generated bilingual messages..."]
}
```

### Configuration Parameters

- **number_of_messages**: Total messages to send (1-1000)
- **wait_time_seconds**: Delay between messages (0.1-10.0s)
- **window_title_regex**: Pattern for Copilot window detection
- **text_input_patterns**: UI element patterns for text input field
- **send_button_patterns**: UI element patterns for send button
- **sample_messages**: Pre-generated bilingual test messages

### Configuration Management

The config system provides:
- Automatic validation of all parameters
- JSON serialization for easy sharing
- Runtime parameter modification via GUI
- Fallback to sensible defaults

## Testing

The repository includes a comprehensive test suite:

```bash
# Run all tests
python .test/run_tests.py

# Run specific test modules
python -m unittest .test.test_config
python -m unittest .test.test_main
python -m unittest .test.test_generator
```

### Test Coverage

- **Config System**: Serialization, validation, file I/O
- **Main Integration**: Entry point, argument parsing, logging
- **Message Generation**: Bilingual content, character sets
- **Installation Validation**: Module imports, dependencies

Current test status: ✅ 18/18 tests passing

## Error Handling

The application includes comprehensive error handling:

- **Window Detection**: Validates Copilot application is running
- **Element Validation**: Checks UI elements exist and are enabled with combined criteria
- **Debug Integration**: Automatically invokes debug script on failures
- **Graceful Recovery**: Continues operation despite individual message failures
- **Logging**: All errors logged to both console and session.log

## Exit Codes

- `0`: Success (all or partial messages sent)
- `1`: Critical failure (no messages sent, missing dependencies, etc.)

## Development

### Code Quality

The project includes automated code quality checks:

```bash
# Format code
black *.py

# Sort imports  
isort *.py

# Lint code
flake8 --max-line-length=120 *.py
```

### Testing

While full functionality requires Windows and Copilot, the scripts include cross-platform compatibility checks and can be syntax-validated on any platform.

### Clean Install Verification

```bash
# Verify clean installation
python .test/run_tests.py

# Check all dependencies
python -c "from config import Config; print('✅ All imports successful')"
```

## Troubleshooting

1. **"pywinauto not available"**: Install with `pip install -r requirements.txt`
2. **"Window not found"**: Ensure Microsoft Copilot is running and visible
3. **"Elements not found"**: Check debug output from automatic control tree dumps
4. **"PySide6 not available"**: Install GUI dependencies with `pip install PySide6`
5. **Performance issues**: Adjust `wait_time_seconds` and `number_of_messages` in config

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Ensure CI/CD pipeline passes (run `python .test/run_tests.py`)
5. Submit a pull request

## License

This project is for educational and testing purposes.
