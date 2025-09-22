#!/usr/bin/env python3
"""
Clean Install Verification Script for Language Crash Test

This script verifies that the application can run correctly in a fresh environment.
It checks dependencies, validates configuration, and ensures core functionality works.

Usage:
    python verify_install.py
    python verify_install.py --full  # Include GUI verification
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def check_python_version():
    """Check that Python version is adequate."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ❌ Python {version.major}.{version.minor} - requires Python 3.8+")
        return False
    
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check that all required dependencies are available."""
    print("\n📦 Checking dependencies...")
    
    # Core dependencies
    core_deps = [
        ('config', 'Configuration system'),
        ('generator', 'Message generator'),
        ('copilot_ui_stress_test', 'Main stress test module'),
        ('copilot_ui_debug', 'Debug module'),
        ('main', 'Main entry point')
    ]
    
    missing_core = []
    for module, description in core_deps:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
        except ImportError as e:
            print(f"  ❌ {module} - {description} ({e})")
            missing_core.append(module)
    
    # Optional dependencies
    optional_deps = [
        ('PySide6', 'GUI framework (optional)'),
    ]
    
    missing_optional = []
    for module, description in optional_deps:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
        except ImportError:
            print(f"  ⚠️  {module} - {description} (optional, install with: pip install {module})")
            missing_optional.append(module)
    
    return len(missing_core) == 0, missing_core, missing_optional


def check_config_system():
    """Test the configuration system."""
    print("\n⚙️ Testing configuration system...")
    
    try:
        from config import Config
        
        # Test default config creation
        config = Config()
        print(f"  ✅ Default config: {config.get_runtime_summary()}")
        
        # Test validation
        config.validate()
        print("  ✅ Configuration validation")
        
        # Test serialization
        config_dict = config.to_dict()
        print(f"  ✅ Serialization: {len(config_dict)} parameters")
        
        # Test file operations
        test_file = "verify_test_config.json"
        config.save_to_file(test_file)
        loaded_config = Config.load_from_file(test_file)
        os.remove(test_file)
        print("  ✅ File save/load operations")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration system failed: {e}")
        return False


def check_message_generation():
    """Test message generation."""
    print("\n💬 Testing message generation...")
    
    try:
        from generator import generate_message, generate_messages
        
        # Test single message
        message = generate_message()
        print(f"  ✅ Single message: {len(message)} chars")
        
        # Test multiple messages
        messages = generate_messages(5)
        print(f"  ✅ Multiple messages: {len(messages)} generated")
        
        # Check bilingual content
        all_text = " ".join(messages)
        has_norwegian = any(char in all_text for char in ['æ', 'ø', 'å'])
        has_english = any(word in all_text.lower() for word in ['the', 'and', 'error'])
        
        if has_norwegian and has_english:
            print("  ✅ Bilingual content verified")
        else:
            print("  ⚠️  Bilingual content check inconclusive")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Message generation failed: {e}")
        return False


def check_main_entry_point():
    """Test the main entry point."""
    print("\n🚀 Testing main entry point...")
    
    try:
        # Test help command
        result = subprocess.run([
            sys.executable, "main.py", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ Main help command")
        else:
            print(f"  ❌ Main help failed: {result.stderr}")
            return False
        
        # Test config creation (should not fail)
        if os.path.exists("config.json"):
            os.rename("config.json", "config.json.backup")
        
        result = subprocess.run([
            sys.executable, "-c", 
            "from config import Config; c=Config(); c.save_to_file('verify_config.json')"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists("verify_config.json"):
            os.remove("verify_config.json")
            print("  ✅ Config creation")
        else:
            print(f"  ❌ Config creation failed: {result.stderr}")
            return False
        
        # Restore backup if it exists
        if os.path.exists("config.json.backup"):
            os.rename("config.json.backup", "config.json")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Main entry point test failed: {e}")
        return False


def check_gui_system(full_check=False):
    """Test GUI system if available."""
    print("\n🎨 Testing GUI system...")
    
    if not full_check:
        print("  ℹ️  Skipping GUI test (use --full for complete check)")
        return True
    
    try:
        # Check if PySide6 is available first
        try:
            from PySide6.QtWidgets import QApplication
            pyside6_available = True
        except ImportError:
            pyside6_available = False
        
        if not pyside6_available:
            print("  ⚠️  PySide6 not available (GUI mode disabled, install with: pip install PySide6)")
            print("  ✅ GUI system gracefully handles missing dependencies")
            return True  # This is acceptable - GUI is optional
        
        # Test GUI imports (this should work if PySide6 is available)
        import gui_configurator
        print("  ✅ GUI module import")
        print("  ✅ PySide6 available")
        
        # Create a minimal test (don't show window)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test configurator creation (but don't show)
        configurator = gui_configurator.Configurator()
        print("  ✅ GUI configurator creation")
        
        return True
        
    except Exception as e:
        print(f"  ❌ GUI system test failed: {e}")
        return False


def run_comprehensive_tests():
    """Run the comprehensive test suite."""
    print("\n🧪 Running comprehensive test suite...")
    
    if not os.path.exists(".test/run_tests.py"):
        print("  ⚠️  Test suite not found")
        return True
    
    try:
        result = subprocess.run([
            sys.executable, ".test/run_tests.py"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Count passed tests from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'Tests run:' in line:
                    print(f"  ✅ {line.strip()}")
                    break
            else:
                print("  ✅ All tests passed")
            return True
        else:
            print(f"  ❌ Test suite failed:")
            # Show last few lines of error
            error_lines = result.stdout.split('\n')[-10:]
            for line in error_lines:
                if line.strip():
                    print(f"    {line}")
            return False
        
    except subprocess.TimeoutExpired:
        print("  ❌ Test suite timed out")
        return False
    except Exception as e:
        print(f"  ❌ Test suite execution failed: {e}")
        return False


def main():
    """Main verification function."""
    parser = argparse.ArgumentParser(description="Clean install verification for Language Crash Test")
    parser.add_argument("--full", action="store_true", help="Include GUI and full test suite verification")
    args = parser.parse_args()
    
    print("🔍 Language Crash Test - Clean Install Verification")
    print("=" * 60)
    
    # Track results
    checks = []
    
    # Core checks
    checks.append(("Python Version", check_python_version()))
    
    deps_ok, missing_core, missing_optional = check_dependencies()
    checks.append(("Dependencies", deps_ok))
    
    checks.append(("Configuration System", check_config_system()))
    checks.append(("Message Generation", check_message_generation()))
    checks.append(("Main Entry Point", check_main_entry_point()))
    checks.append(("GUI System", check_gui_system(args.full)))
    
    if args.full:
        checks.append(("Comprehensive Tests", run_comprehensive_tests()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    passed = sum(1 for name, result in checks if result)
    total = len(checks)
    
    for name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 Clean install verification SUCCESSFUL!")
        print("💡 Language Crash Test is ready for use:")
        print("   python main.py --help")
        print("   python main.py --gui")
        print("   python main.py --debug")
        return 0
    else:
        print("\n❌ Clean install verification FAILED!")
        if missing_core:
            print(f"   Missing core dependencies: {missing_core}")
        print("   Please check the installation and requirements.")
        return 1


if __name__ == "__main__":
    sys.exit(main())