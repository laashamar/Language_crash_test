# Language_crash_test
Stress-testing Copilot UI via bilingual automation script

## Overview

This repository contains Python scripts for automated stress testing of the Microsoft Copilot desktop application. The scripts simulate realistic user interactions by sending bilingual messages (English and Norwegian) with emojis and special characters to test the application's performance and stability.

## Features

- **Bilingual Testing**: Messages in both English and Norwegian with special characters (æ, ø, å)
- **Robust UI Element Detection**: Primary and fallback methods for locating text input and send button
- **Automatic Debug Integration**: Required fallback mechanism that dumps UI control tree when elements fail
- **Comprehensive Error Handling**: Graceful handling of all UI automation exceptions
- **CI/CD Pipeline**: Automated testing and validation via GitHub Actions
- **Configurable Parameters**: Customizable message count and timing

## Requirements

- Windows operating system
- Microsoft Copilot for Windows application
- Python 3.8 or higher
- pywinauto library

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Ensure Microsoft Copilot is running, then execute:

```bash
python copilot_ui_stress_test.py
```

### Debug Mode

To inspect the UI control structure:

```bash
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
   - Number of messages (default: 10)
   - Wait time between messages (default: 0.5s)

#### Automatic Triggers

- **Push to main/develop**: Runs syntax and quality checks
- **Pull requests**: Full validation suite
- **Commit messages with `[run-stress-test]`**: Triggers Windows stress test

## Configuration

Key configuration parameters in `copilot_ui_stress_test.py`:

```python
NUMBER_OF_MESSAGES = 50        # Total messages to send
WAIT_TIME_SECONDS = 0.5        # Delay between messages
WINDOW_TITLE_REGEX = r"^Copilot.*"  # Window detection pattern
```

## Error Handling

The script includes comprehensive error handling:

- **Window Detection**: Validates Copilot application is running
- **Element Validation**: Checks UI elements exist and are enabled
- **Debug Integration**: Automatically invokes debug script on failures
- **Graceful Recovery**: Continues operation despite individual message failures

## Exit Codes

- `0`: Success (all or partial messages sent)
- `1`: Critical failure (no messages sent, missing dependencies, etc.)

## Development

### Code Quality

The project includes automated code quality checks:

```bash
# Format code
black copilot_ui_stress_test.py copilot_ui_debug.py

# Sort imports
isort copilot_ui_stress_test.py copilot_ui_debug.py

# Lint code
flake8 --max-line-length=120 copilot_ui_stress_test.py copilot_ui_debug.py
```

### Testing

While full functionality requires Windows and Copilot, the scripts include cross-platform compatibility checks and can be syntax-validated on any platform.

## Troubleshooting

1. **"pywinauto not available"**: Install requirements with `pip install -r requirements.txt`
2. **"Window not found"**: Ensure Microsoft Copilot is running and visible
3. **"Elements not found"**: Check debug output from automatic control tree dumps
4. **Performance issues**: Adjust `WAIT_TIME_SECONDS` and `NUMBER_OF_MESSAGES`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Ensure CI/CD pipeline passes
5. Submit a pull request

## License

This project is for educational and testing purposes.
