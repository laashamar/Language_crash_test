#!/usr/bin/env python3
"""
Test runner for all Language Crash Test test suites.

Runs all tests and provides a comprehensive report of test results.
Validates core functionality, integration, and error handling.
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
test_dir = Path(__file__).parent
parent_dir = test_dir.parent
sys.path.insert(0, str(parent_dir))

# Import test modules
try:
    from test_config import TestConfig
    from test_main import TestMainIntegration, TestArgumentParsing
    from test_generator import TestGenerator
    print("✅ All test modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import test modules: {e}")
    sys.exit(1)


def run_all_tests():
    """Run all test suites and return results."""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestConfig,
        TestMainIntegration,
        TestArgumentParsing,
        TestGenerator
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def validate_installation():
    """Validate that all required modules can be imported."""
    print("🔍 Validating installation...")
    
    required_modules = [
        'language_crash_test.config',
        'language_crash_test.generator', 
        'language_crash_test.automation',
        'language_crash_test.debug',
        'main'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module} - {e}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing modules: {missing_modules}")
        return False
    
    print("✅ All required modules available")
    return True


def check_config_functionality():
    """Quick check that config system works."""
    print("\n🔧 Testing config functionality...")
    
    try:
        from language_crash_test.config import Config
        
        # Test default config
        config = Config()
        print(f"  ✅ Default config: {config.get_runtime_summary()}")
        
        # Test serialization
        config_dict = config.to_dict()
        print(f"  ✅ Serialization: {len(config_dict)} keys")
        
        # Test validation
        config.validate()
        print("  ✅ Validation passed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False


def main():
    """Main test runner function."""
    print("🧪 Language Crash Test - Test Suite Runner")
    print("=" * 50)
    
    # Change to parent directory for correct imports
    os.chdir(parent_dir)
    
    # Validate installation
    if not validate_installation():
        print("\n❌ Installation validation failed")
        sys.exit(1)
    
    # Quick config check
    if not check_config_functionality():
        print("\n❌ Config functionality check failed")
        sys.exit(1)
    
    print("\n🚀 Running comprehensive test suite...")
    print("=" * 50)
    
    # Run all tests
    result = run_all_tests()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Skipped: {len(result.skipped)}")
        
        print("\n🎉 Language Crash Test is ready for use!")
        print("💡 You can now run:")
        print("   python main.py --help")
        print("   python main.py --gui")
        print("   python main.py --debug")
        
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        if result.failures:
            print("\n📋 Failures:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback.splitlines()[-1]}")
        
        if result.errors:
            print("\n📋 Errors:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback.splitlines()[-1]}")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())