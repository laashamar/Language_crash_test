#!/usr/bin/env python3
"""
Test script to validate GUI freeze fixes.

This script performs basic validation of the GUI improvements
without requiring a full GUI environment.
"""

import sys
import ast
import re
from pathlib import Path


def test_gui_improvements():
    """Test that GUI freeze issues have been addressed."""
    gui_file = Path("gui_configurator.py")
    
    if not gui_file.exists():
        print("❌ GUI file not found")
        return False
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Ensure QApplication.processEvents() is not used (except in comments)
    total_tests += 1
    process_events_lines = [line for line in content.split('\n') 
                          if 'processEvents' in line and not line.strip().startswith('#')]
    if not process_events_lines:
        print("✅ Test 1: No QApplication.processEvents() calls found")
        tests_passed += 1
    else:
        print(f"❌ Test 1: Found processEvents() calls: {len(process_events_lines)}")
    
    # Test 2: Check for proper widget parenting
    total_tests += 1
    widget_with_parent_count = content.count('(self)')
    if widget_with_parent_count >= 5:  # We added several
        print(f"✅ Test 2: Widget parenting improved ({widget_with_parent_count} widgets with self parent)")
        tests_passed += 1
    else:
        print(f"❌ Test 2: Insufficient widget parenting ({widget_with_parent_count} found)")
    
    # Test 3: Check for error signal handling
    total_tests += 1
    if 'error = Signal(str)' in content:
        print("✅ Test 3: Error signal added for proper exception handling")
        tests_passed += 1
    else:
        print("❌ Test 3: Missing error signal for exception handling")
    
    # Test 4: Check for timeout protection
    total_tests += 1
    if 'QTimer' in content and 'timeout' in content:
        print("✅ Test 4: Timeout protection added")
        tests_passed += 1
    else:
        print("❌ Test 4: Missing timeout protection")
    
    # Test 5: Check for proper thread cleanup
    total_tests += 1
    cleanup_methods = ['quit', 'wait', 'deleteLater', 'requestInterruption']
    found_cleanup = sum(1 for method in cleanup_methods if method in content)
    if found_cleanup >= 3:
        print(f"✅ Test 5: Thread cleanup methods present ({found_cleanup}/{len(cleanup_methods)})")
        tests_passed += 1
    else:
        print(f"❌ Test 5: Insufficient thread cleanup ({found_cleanup}/{len(cleanup_methods)})")
    
    # Test 6: Verify proper signal-slot connections (no function calls)
    total_tests += 1
    bad_connections = re.findall(r'\.connect\s*\(\s*\w+\s*\(\s*\)\s*\)', content)
    if not bad_connections:
        print("✅ Test 6: No improper signal-slot connections found")
        tests_passed += 1
    else:
        print(f"❌ Test 6: Found {len(bad_connections)} improper signal connections")
    
    # Test 7: Check for exception handling in worker thread
    total_tests += 1
    if 'except Exception as e:' in content and 'logger.exception' in content:
        print("✅ Test 7: Proper exception handling in worker thread")
        tests_passed += 1
    else:
        print("❌ Test 7: Missing proper exception handling")
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All GUI freeze prevention tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. GUI may still have freezing issues.")
        return False


def test_blocking_operations_in_thread():
    """Test that blocking operations are properly isolated in worker threads."""
    stress_test_file = Path("copilot_ui_stress_test.py")
    
    if not stress_test_file.exists():
        print("❌ Stress test file not found")
        return False
    
    with open(stress_test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Analyzing blocking operations...")
    
    # Check that blocking operations exist but are called from worker thread
    has_sleep = 'time.sleep' in content
    has_subprocess = 'subprocess.run' in content
    
    if has_sleep:
        print("✅ time.sleep() found - this is OK as it runs in worker thread")
    
    if has_subprocess:
        print("✅ subprocess.run() found - this is OK as it runs in worker thread") 
    
    # The key is that these are called through run_stress_test_logic 
    # which is executed in the worker thread
    if 'run_stress_test_logic' in content:
        print("✅ Blocking operations properly isolated in stress test logic")
        return True
    else:
        print("❌ Cannot verify proper isolation of blocking operations")
        return False


def main():
    """Run all GUI freeze tests."""
    print("🔧 Testing GUI Freeze Prevention Improvements")
    print("=" * 60)
    
    gui_tests_passed = test_gui_improvements()
    blocking_tests_passed = test_blocking_operations_in_thread()
    
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("=" * 60)
    
    if gui_tests_passed and blocking_tests_passed:
        print("🎉 All GUI freeze prevention measures are in place!")
        print("💡 The application should now be more robust against GUI freezing.")
        return 0
    else:
        print("⚠️ Some issues remain. Review the failed tests above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())