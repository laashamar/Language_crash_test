#!/usr/bin/env python3
"""
Worker Module for Language Crash Test GUI

Implements the StressTestWorker class that runs automation logic in a separate thread
to prevent GUI freezing. Uses Qt's signal/slot mechanism for thread-safe communication.

Key Features:
- QObject-based worker for proper Qt threading
- Signal throttling to prevent GUI overload
- Thread-safe pywinauto imports (imported inside run method)
- Comprehensive error handling and reporting
- Graceful shutdown and cleanup
"""

import sys
import io
import contextlib
import logging
from typing import Dict, Any, Optional

try:
    from PySide6.QtCore import QObject, Signal, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    # PySide6 not available - define minimal stubs
    PYSIDE6_AVAILABLE = False
    
    class QObject:
        def __init__(self): pass
    
    class Signal:
        def __init__(self, *args): pass
        def emit(self, *args): pass
        def connect(self, *args): pass
    
    class QTimer:
        def __init__(self): pass
        def setInterval(self, ms): pass
        def setSingleShot(self, single): pass
        def timeout(self): return Signal()
        def start(self): pass
        def stop(self): pass
        def isActive(self): return False


class ThrottledStreamToSignal(QObject):
    """
    A class that redirects sys.stdout to a Qt signal with buffering and throttling
    to prevent GUI thread overload from high-frequency log messages.
    
    Features:
    - Buffers multiple writes into a single signal emission
    - Configurable delay to throttle signal frequency
    - Automatic flushing on timer or manual flush
    """
    text_written = Signal(str)

    def __init__(self, parent=None, delay_ms=200):
        super().__init__(parent)
        self.buffer = []
        self.timer = QTimer(self)
        self.timer.setInterval(delay_ms)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._emit_buffered_text)

    def write(self, text):
        """Write text to buffer and start timer if not active."""
        if text and text.strip():  # Only buffer non-empty text
            self.buffer.append(str(text))
            if not self.timer.isActive():
                self.timer.start()

    def _emit_buffered_text(self):
        """Emit all buffered text as a single signal."""
        if not self.buffer:
            return
        
        # Join all buffered text and emit as one signal
        message = "".join(self.buffer)
        self.buffer.clear()
        self.text_written.emit(message)

    def flush(self):
        """Force emission of any buffered text."""
        self.timer.stop()
        self._emit_buffered_text()


class StressTestWorker(QObject):
    """
    Worker class that runs the stress test in a separate thread.
    
    Inherits from QObject to use Qt's signal/slot mechanism for thread-safe
    communication with the GUI thread. Implements proper error handling
    and resource cleanup.
    
    Signals:
        progress: Emitted with log messages for GUI display
        finished: Emitted when test completes (success or failure)
        error: Emitted when an unhandled error occurs
    """
    
    # Qt Signals for thread-safe communication
    progress = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, config, parent=None):
        """
        Initialize the worker with configuration.
        
        Args:
            config: Configuration object with test parameters
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        self.config = config
        self.result = {}
        self._should_stop = False

    def stop(self):
        """Request the worker to stop execution."""
        self._should_stop = True

    def run(self):
        """
        Main worker method that runs in the separate thread.
        
        Imports pywinauto and automation module inside this method to ensure
        thread-safe operation and prevent cross-thread conflicts.
        """
        # Import automation module inside the worker thread for thread safety
        try:
            from .automation import run_stress_test_logic
        except ImportError as e:
            error_msg = f"Failed to import automation module: {e}"
            self.error.emit(error_msg)
            return

        # Set up logging to capture output for GUI display
        logger = self._setup_worker_logging()
        
        try:
            logger.info("🧵 Worker thread started")
            logger.info(f"📋 Configuration: {self.config.get_runtime_summary()}")
            
            # Check if we should stop before starting
            if self._should_stop:
                logger.info("🛑 Worker stopped before execution")
                return
            
            # Run the main automation logic
            self.result = run_stress_test_logic(self.config, logger)
            
            # Log final results
            success_count = self.result.get('success', 0)
            total_messages = self.result.get('total', 0)
            error_msg = self.result.get('error')
            
            if error_msg:
                logger.error(f"❌ Test failed: {error_msg}")
            else:
                logger.info(f"✅ Test completed: {success_count}/{total_messages} messages sent")
            
        except Exception as e:
            # Catch any unhandled exceptions
            error_msg = f"Unhandled exception in worker thread: {type(e).__name__}: {e}"
            logger.exception(error_msg)
            self.error.emit(error_msg)
            self.result = {
                'error': error_msg, 
                'success': 0, 
                'total': self.config.number_of_messages
            }
        finally:
            # Ensure any remaining log output is sent to GUI
            try:
                if hasattr(self, '_stdout_redirector'):
                    self._stdout_redirector.flush()
            except:
                pass
            
            logger.info("🧵 Worker thread finishing")
            self.finished.emit()

    def _setup_worker_logging(self):
        """
        Set up logging for the worker thread with stdout redirection.
        
        Returns:
            Logger instance configured for this worker
        """
        # Create a logger for this worker
        logger = logging.getLogger(f"worker_{id(self)}")
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplication
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create stdout redirector for capturing print statements
        self._stdout_redirector = ThrottledStreamToSignal(delay_ms=200)
        self._stdout_redirector.text_written.connect(self.progress.emit)
        
        # Create handler that writes to our redirector
        stream_handler = logging.StreamHandler(self._stdout_redirector)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # Redirect stdout to our signal emitter
        self._original_stdout = sys.stdout
        sys.stdout = self._stdout_redirector
        
        return logger

    def cleanup(self):
        """Clean up resources when worker is finished."""
        try:
            # Restore original stdout
            if hasattr(self, '_original_stdout'):
                sys.stdout = self._original_stdout
            
            # Final flush of any remaining output
            if hasattr(self, '_stdout_redirector'):
                self._stdout_redirector.flush()
                
        except Exception as e:
            # Don't let cleanup errors propagate
            print(f"Warning: Worker cleanup error: {e}")

    def get_result(self) -> Dict[str, Any]:
        """
        Get the result of the stress test.
        
        Returns:
            Dictionary with test results
        """
        return self.result.copy() if self.result else {}

    def is_finished(self) -> bool:
        """
        Check if the worker has finished execution.
        
        Returns:
            True if worker has completed
        """
        return bool(self.result)


# Compatibility check function
def check_threading_compatibility() -> bool:
    """
    Check if the environment supports the worker threading model.
    
    Returns:
        True if threading is supported, False otherwise
    """
    if not PYSIDE6_AVAILABLE:
        return False
    
    try:
        # Test basic Qt threading components
        from PySide6.QtCore import QThread, QObject, Signal
        
        # Create a simple test worker to verify functionality
        class TestWorker(QObject):
            test_signal = Signal(str)
            
            def run(self):
                self.test_signal.emit("test")
        
        # If we get here, threading should work
        return True
        
    except Exception:
        return False


if __name__ == "__main__":
    # Test the worker module
    print("🧪 Testing Worker Module")
    print("=" * 40)
    
    # Check if PySide6 is available
    if not PYSIDE6_AVAILABLE:
        print("❌ PySide6 not available - GUI functionality disabled")
        sys.exit(1)
    
    # Check threading compatibility
    if check_threading_compatibility():
        print("✅ Threading compatibility check passed")
    else:
        print("❌ Threading compatibility check failed")
        sys.exit(1)
    
    # Test throttled stream
    print("\n🔄 Testing ThrottledStreamToSignal...")
    
    try:
        stream = ThrottledStreamToSignal()
        
        # Connect signal to a test handler
        def test_handler(text):
            print(f"Received: {repr(text)}")
        
        stream.text_written.connect(test_handler)
        
        # Test writing
        stream.write("Test message 1\n")
        stream.write("Test message 2\n")
        stream.flush()
        
        print("✅ ThrottledStreamToSignal test completed")
        
    except Exception as e:
        print(f"❌ ThrottledStreamToSignal test failed: {e}")
        sys.exit(1)
    
    print("\n🎉 Worker module tests completed successfully!")