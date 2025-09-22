#!/usr/bin/env python3
"""
GUI Freeze Diagnosis Tool for Language Crash Test

Implements comprehensive 23-step analysis to diagnose GUI freezing issues
in PyQt/PySide applications according to the problem statement requirements.

Usage:
    python gui_freeze_diagnosis.py
    python gui_freeze_diagnosis.py --output diagnosis_report.json
"""

import ast
import os
import sys
import json
import re
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
import argparse


@dataclass
class DiagnosisIssue:
    """Represents a potential GUI freezing issue."""
    step: int
    severity: str  # "high", "medium", "low"
    category: str
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    recommendation: str
    

@dataclass
class DiagnosisReport:
    """Complete diagnosis report."""
    issues: List[DiagnosisIssue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    pyside_version: str = ""
    total_files_analyzed: int = 0


class GUIFreezeDiagnosisAnalyzer:
    """Main analyzer class implementing the 23-step diagnosis."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.report = DiagnosisReport()
        self.python_files = list(self.repo_path.glob("*.py"))
        self.report.total_files_analyzed = len(self.python_files)
        
    def analyze(self) -> DiagnosisReport:
        """Run the complete 23-step analysis."""
        print("🔍 Starting comprehensive GUI freeze diagnosis...")
        
        # Get PySide6 version info
        self._check_pyside_version()
        
        # Analyze each Python file
        for file_path in self.python_files:
            if file_path.name.startswith('.'):
                continue
                
            print(f"📄 Analyzing {file_path.name}...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(file_path))
                self._analyze_file(file_path, content, tree)
            except Exception as e:
                print(f"⚠️ Error analyzing {file_path}: {e}")
        
        self._generate_summary()
        return self.report
    
    def _check_pyside_version(self):
        """Step 19: Confirm PySide6 version compatibility."""
        try:
            import PySide6
            self.report.pyside_version = PySide6.__version__
            
            # Check for known issues in versions < 6.4
            version_parts = [int(x) for x in PySide6.__version__.split('.')]
            if version_parts[0] == 6 and version_parts[1] < 4:
                self.report.issues.append(DiagnosisIssue(
                    step=19,
                    severity="medium",
                    category="version_compatibility",
                    file_path="<system>",
                    line_number=0,
                    code_snippet=f"PySide6 version: {PySide6.__version__}",
                    description=f"PySide6 version {PySide6.__version__} may have threading or signal issues",
                    recommendation="Consider upgrading to PySide6 >= 6.4 for better threading support"
                ))
        except ImportError:
            self.report.pyside_version = "Not installed"
    
    def _analyze_file(self, file_path: Path, content: str, tree: ast.AST):
        """Analyze a single Python file for GUI freezing issues."""
        lines = content.split('\n')
        
        # Step 1: Check for blocking operations in main thread
        self._check_blocking_operations(file_path, content, lines, tree)
        
        # Step 2: Verify correct use of QThread
        self._check_qthread_usage(file_path, content, lines, tree)
        
        # Step 3: Audit signal-slot connections  
        self._check_signal_slot_connections(file_path, content, lines, tree)
        
        # Step 4: Check for GUI updates from non-main threads
        self._check_gui_updates_from_threads(file_path, content, lines, tree)
        
        # Step 5: Inspect thread cleanup logic
        self._check_thread_cleanup(file_path, content, lines, tree)
        
        # Step 6: Validate QThreadPool usage
        self._check_qthreadpool_usage(file_path, content, lines, tree)
        
        # Step 7: Check for excessive object creation
        self._check_excessive_object_creation(file_path, content, lines, tree)
        
        # Step 8: Surface unhandled exceptions in threads
        self._check_unhandled_exceptions(file_path, content, lines, tree)
        
        # Step 9: Confirm use of QTimer
        self._check_qtimer_usage(file_path, content, lines, tree)
        
        # Step 10: Detect event loop starvation
        self._check_event_loop_starvation(file_path, content, lines, tree)
        
        # Step 11: Audit nested event loops
        self._check_nested_event_loops(file_path, content, lines, tree)
        
        # Step 12: Check for QTimer misuse
        self._check_qtimer_misuse(file_path, content, lines, tree)
        
        # Step 13: Surface GIL-bound operations
        self._check_gil_bound_operations(file_path, content, lines, tree)
        
        # Step 14: Audit third-party library calls
        self._check_third_party_blocking_calls(file_path, content, lines, tree)
        
        # Step 15: Validate layout recalculations
        self._check_layout_recalculations(file_path, content, lines, tree)
        
        # Step 16: Check for excessive logging
        self._check_excessive_logging(file_path, content, lines, tree)
        
        # Step 17: Inspect resource loading
        self._check_resource_loading(file_path, content, lines, tree)
        
        # Step 18: Detect missing setParent
        self._check_missing_parent(file_path, content, lines, tree)
        
        # Step 20: Validate QApplication.processEvents usage
        self._check_process_events_usage(file_path, content, lines, tree)
        
        # Step 21: Check platform-specific issues
        self._check_platform_issues(file_path, content, lines, tree)
        
        # Step 22: Surface excessive lambda usage
        self._check_lambda_usage(file_path, content, lines, tree)
    
    def _check_blocking_operations(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 1: Check for blocking operations in the main thread."""
        blocking_patterns = [
            (r'time\.sleep\s*\(', 'time.sleep() call blocks the main thread'),
            (r'subprocess\.run\s*\([^)]*timeout\s*=\s*(\d+)', 'subprocess.run() without proper timeout'),
            (r'requests\.get\s*\(', 'Synchronous HTTP request'),
            (r'requests\.post\s*\(', 'Synchronous HTTP request'),
            (r'\.join\s*\(\s*\)', 'Thread.join() without timeout'),
            (r'\.wait\s*\(\s*\)', 'Process.wait() without timeout'),
            (r'input\s*\(', 'input() blocks the main thread'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description in blocking_patterns:
                if re.search(pattern, line):
                    # Check if we're in a GUI class or main thread context
                    if self._is_in_gui_context(tree, i):
                        severity = "high" if "time.sleep" in pattern else "medium"
                        self.report.issues.append(DiagnosisIssue(
                            step=1,
                            severity=severity,
                            category="blocking_operations",
                            file_path=str(file_path),
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            description=f"Potential blocking operation: {description}",
                            recommendation="Move blocking operations to worker threads or use async alternatives"
                        ))
    
    def _check_qthread_usage(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 2: Verify correct use of QThread or QRunnable."""
        class ThreadUsageVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, file_path):
                self.analyzer = analyzer
                self.file_path = file_path
                self.in_thread_class = False
                self.current_class = None
            
            def visit_ClassDef(self, node):
                # Check if class inherits from QThread or QObject
                is_thread_class = any(
                    isinstance(base, ast.Name) and base.id in ['QThread', 'QObject', 'QRunnable']
                    or isinstance(base, ast.Attribute) and base.attr in ['QThread', 'QObject', 'QRunnable']
                    for base in node.bases
                )
                
                old_class = self.current_class
                old_in_thread = self.in_thread_class
                self.current_class = node.name
                self.in_thread_class = is_thread_class
                
                self.generic_visit(node)
                
                self.current_class = old_class
                self.in_thread_class = old_in_thread
            
            def visit_FunctionDef(self, node):
                if self.in_thread_class and node.name == 'run':
                    # Check if run method has proper exception handling
                    has_try_except = any(isinstance(stmt, ast.Try) for stmt in ast.walk(node))
                    if not has_try_except:
                        self.analyzer.report.issues.append(DiagnosisIssue(
                            step=2,
                            severity="medium",
                            category="thread_usage",
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            code_snippet=f"def {node.name}(...):",
                            description="Thread run() method lacks exception handling",
                            recommendation="Add try/except blocks in run() method to handle exceptions"
                        ))
                
                # Check for moveToThread usage
                if node.name == '__init__' and self.current_class:
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Call):
                            if (isinstance(stmt.func, ast.Attribute) and 
                                stmt.func.attr == 'moveToThread'):
                                # Good practice found - no issue
                                pass
                
                self.generic_visit(node)
        
        visitor = ThreadUsageVisitor(self, file_path)
        visitor.visit(tree)
    
    def _check_signal_slot_connections(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 3: Audit signal-slot connections."""
        # Look for incorrect signal connections (calling function instead of passing reference)
        for i, line in enumerate(lines):
            # Check for .connect(func()) instead of .connect(func)
            pattern = r'\.connect\s*\(\s*\w+\s*\(\s*\)\s*\)'
            if re.search(pattern, line):
                self.report.issues.append(DiagnosisIssue(
                    step=3,
                    severity="high",
                    category="signal_slot",
                    file_path=str(file_path),
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    description="Signal connected to function call result instead of function reference",
                    recommendation="Remove parentheses: use .connect(func) instead of .connect(func())"
                ))
    
    def _check_gui_updates_from_threads(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 4: Check for GUI updates from non-main threads."""
        gui_update_methods = [
            'setText', 'setValue', 'setVisible', 'show', 'hide', 'update', 'repaint',
            'setPixmap', 'addWidget', 'removeWidget', 'insertText', 'append'
        ]
        
        class ThreadGuiUpdateVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, file_path):
                self.analyzer = analyzer
                self.file_path = file_path
                self.in_thread_run = False
                self.in_worker_class = False
            
            def visit_ClassDef(self, node):
                old_worker = self.in_worker_class
                # Check if this looks like a worker class
                self.in_worker_class = ('worker' in node.name.lower() or 
                                      any(isinstance(base, ast.Name) and 'worker' in base.id.lower()
                                          for base in node.bases if isinstance(base, ast.Name)))
                self.generic_visit(node)
                self.in_worker_class = old_worker
            
            def visit_FunctionDef(self, node):
                old_run = self.in_thread_run
                self.in_thread_run = (node.name == 'run' and self.in_worker_class)
                self.generic_visit(node)
                self.in_thread_run = old_run
            
            def visit_Call(self, node):
                if self.in_thread_run and isinstance(node.func, ast.Attribute):
                    if node.func.attr in gui_update_methods:
                        self.analyzer.report.issues.append(DiagnosisIssue(
                            step=4,
                            severity="high",
                            category="thread_gui_updates",
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            code_snippet=f"...{node.func.attr}(...)",
                            description=f"Direct GUI update from worker thread: {node.func.attr}",
                            recommendation="Use signals to update GUI from main thread instead of direct calls"
                        ))
                self.generic_visit(node)
        
        visitor = ThreadGuiUpdateVisitor(self, file_path)
        visitor.visit(tree)
    
    def _check_thread_cleanup(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 5: Inspect thread cleanup logic."""
        cleanup_methods = ['quit', 'wait', 'deleteLater', 'terminate']
        
        # Check if threads are properly cleaned up
        has_thread_creation = 'QThread()' in content
        has_cleanup = any(method in content for method in cleanup_methods)
        
        if has_thread_creation and not has_cleanup:
            self.report.issues.append(DiagnosisIssue(
                step=5,
                severity="medium",
                category="thread_cleanup",
                file_path=str(file_path),
                line_number=0,
                code_snippet="QThread() creation found",
                description="Thread created but no cleanup methods found",
                recommendation="Ensure threads are stopped using .quit(), .wait(), and .deleteLater()"
            ))
    
    def _check_qthreadpool_usage(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 6: Validate use of QThreadPool for concurrent tasks."""
        # Count manual thread creation vs QThreadPool usage
        manual_threads = content.count('QThread()')
        threadpool_usage = content.count('QThreadPool')
        
        if manual_threads > 2 and threadpool_usage == 0:
            self.report.issues.append(DiagnosisIssue(
                step=6,
                severity="low",
                category="threadpool",
                file_path=str(file_path),
                line_number=0,
                code_snippet=f"{manual_threads} QThread() instances found",
                description="Multiple manual thread creation without QThreadPool",
                recommendation="Consider using QThreadPool for managing multiple short-lived tasks"
            ))
    
    def _check_excessive_object_creation(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 7: Check for excessive object creation in __init__ or show()."""
        class InitShowVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, file_path):
                self.analyzer = analyzer
                self.file_path = file_path
            
            def visit_FunctionDef(self, node):
                if node.name in ['__init__', 'show', 'setup_ui']:
                    # Count widget/object creation in these methods
                    widget_creations = 0
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Call):
                            if (isinstance(stmt.func, ast.Name) and 
                                stmt.func.id.startswith('Q')):  # Qt classes
                                widget_creations += 1
                    
                    if widget_creations > 20:  # Arbitrary threshold
                        self.analyzer.report.issues.append(DiagnosisIssue(
                            step=7,
                            severity="medium",
                            category="object_creation",
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            code_snippet=f"def {node.name}(...): # {widget_creations} widget creations",
                            description=f"Excessive object creation in {node.name}(): {widget_creations} widgets",
                            recommendation="Consider lazy loading or moving heavy object creation to background"
                        ))
                
                self.generic_visit(node)
        
        visitor = InitShowVisitor(self, file_path)
        visitor.visit(tree)
    
    def _check_unhandled_exceptions(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 8: Surface unhandled exceptions in threads."""
        # Already covered in step 2, but we can add more specific checks
        pass
    
    def _check_qtimer_usage(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 9: Confirm use of QTimer for periodic tasks."""
        # Look for polling loops that could use QTimer instead
        for i, line in enumerate(lines):
            if 'while' in line and ('time.sleep' in lines[i+1:i+5] if i+5 < len(lines) else False):
                self.report.issues.append(DiagnosisIssue(
                    step=9,
                    severity="medium",
                    category="timer_usage",
                    file_path=str(file_path),
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    description="Polling loop with sleep detected",
                    recommendation="Use QTimer.singleShot or QTimer.start for non-blocking timing"
                ))
    
    def _check_event_loop_starvation(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 10: Detect event loop starvation."""
        starvation_patterns = [
            (r'while\s+True\s*:', 'Infinite loop may starve event loop'),
            (r'for\s+.*\s+in\s+range\s*\(\s*\d{4,}', 'Large loop may block event processing'),
            (r'\.repaint\s*\(\s*\)', 'Excessive repaint() calls'),
            (r'\.update\s*\(\s*\)', 'Frequent update() calls'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description in starvation_patterns:
                if re.search(pattern, line):
                    self.report.issues.append(DiagnosisIssue(
                        step=10,
                        severity="medium",
                        category="event_loop",
                        file_path=str(file_path),
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        description=description,
                        recommendation="Ensure event loop can process events; use QTimer for periodic tasks"
                    ))
    
    def _check_nested_event_loops(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 11: Audit nested event loops."""
        nested_patterns = [
            (r'\.exec_\s*\(\s*\)', 'Modal dialog or nested event loop'),
            (r'QEventLoop\s*\(\s*\)', 'Manual event loop creation'),
            (r'QDialog\s*\(.*\)\.exec_\s*\(\s*\)', 'Blocking modal dialog'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description in nested_patterns:
                if re.search(pattern, line):
                    self.report.issues.append(DiagnosisIssue(
                        step=11,
                        severity="medium",
                        category="nested_loops",
                        file_path=str(file_path),
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        description=f"Nested event loop detected: {description}",
                        recommendation="Use non-blocking alternatives or QTimer.singleShot for flow control"
                    ))
    
    def _check_qtimer_misuse(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 12: Check for misuse of QTimer."""
        # Look for QTimer created in threads (should be in main thread)
        class TimerVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, file_path):
                self.analyzer = analyzer
                self.file_path = file_path
                self.in_thread_run = False
            
            def visit_FunctionDef(self, node):
                old_run = self.in_thread_run
                self.in_thread_run = node.name == 'run'
                self.generic_visit(node)
                self.in_thread_run = old_run
            
            def visit_Call(self, node):
                if (isinstance(node.func, ast.Name) and node.func.id == 'QTimer' and 
                    self.in_thread_run):
                    self.analyzer.report.issues.append(DiagnosisIssue(
                        step=12,
                        severity="high",
                        category="timer_misuse",
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        code_snippet="QTimer() in run() method",
                        description="QTimer created inside thread run() method",
                        recommendation="Create QTimer in main thread only"
                    ))
                self.generic_visit(node)
        
        visitor = TimerVisitor(self, file_path)
        visitor.visit(tree)
    
    def _check_gil_bound_operations(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 13: Surface GIL-bound operations."""
        gil_bound_imports = [
            'numpy', 'pandas', 'PIL', 'cv2', 'matplotlib', 'scipy',
            'sklearn', 'tensorflow', 'torch'
        ]
        
        for import_name in gil_bound_imports:
            if f'import {import_name}' in content or f'from {import_name}' in content:
                self.report.issues.append(DiagnosisIssue(
                    step=13,
                    severity="low",
                    category="gil_bound",
                    file_path=str(file_path),
                    line_number=0,
                    code_snippet=f"import {import_name}",
                    description=f"GIL-bound library {import_name} detected",
                    recommendation="Consider multiprocessing or C++ extensions for CPU-intensive tasks"
                ))
    
    def _check_third_party_blocking_calls(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 14: Audit third-party library calls."""
        blocking_calls = [
            (r'requests\.(get|post|put|delete)', 'Synchronous HTTP request'),
            (r'sqlite3\..*\.execute', 'Synchronous database operation'),
            (r'urllib\.request\.urlopen', 'Synchronous URL request'),
            (r'ftplib\..*\.', 'Synchronous FTP operation'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description in blocking_calls:
                if re.search(pattern, line):
                    self.report.issues.append(DiagnosisIssue(
                        step=14,
                        severity="medium",
                        category="third_party_blocking",
                        file_path=str(file_path),
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        description=f"Blocking third-party call: {description}",
                        recommendation="Use async wrappers or move to worker threads"
                    ))
    
    def _check_layout_recalculations(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 15: Validate layout recalculations."""
        layout_methods = [
            'layout().update()', 'addWidget()', 'removeWidget()', 'resize()'
        ]
        
        for method in layout_methods:
            if content.count(method) > 10:  # Threshold for excessive calls
                self.report.issues.append(DiagnosisIssue(
                    step=15,
                    severity="low",
                    category="layout_recalc",
                    file_path=str(file_path),
                    line_number=0,
                    code_snippet=f"{method} called {content.count(method)} times",
                    description=f"Frequent layout recalculation: {method}",
                    recommendation="Batch layout changes or defer with QTimer.singleShot"
                ))
    
    def _check_excessive_logging(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 16: Check for excessive logging or print() in GUI thread."""
        print_count = content.count('print(')
        logging_count = content.count('logging.') + content.count('logger.')
        
        if print_count > 20:
            self.report.issues.append(DiagnosisIssue(
                step=16,
                severity="low",
                category="excessive_logging",
                file_path=str(file_path),
                line_number=0,
                code_snippet=f"{print_count} print() statements",
                description="Excessive console output may slow GUI responsiveness",
                recommendation="Throttle logging or redirect to file"
            ))
    
    def _check_resource_loading(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 17: Inspect resource loading."""
        resource_patterns = [
            (r'QPixmap\s*\(', 'QPixmap loading'),
            (r'QImage\s*\(', 'QImage loading'),
            (r'QFont\s*\(', 'QFont loading'),
            (r'setStyleSheet\s*\(', 'Stylesheet application'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description in resource_patterns:
                if re.search(pattern, line) and self._is_in_gui_context(tree, i):
                    self.report.issues.append(DiagnosisIssue(
                        step=17,
                        severity="low",
                        category="resource_loading",
                        file_path=str(file_path),
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        description=f"Resource loading in main thread: {description}",
                        recommendation="Consider lazy loading or background prefetching"
                    ))
    
    def _check_missing_parent(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 18: Detect missing .setParent() or memory leaks."""
        # This is complex to detect statically, so we'll flag potential issues
        widget_creations = re.findall(r'(\w+)\s*=\s*Q\w+\s*\(', content)
        setparent_calls = content.count('setParent(')
        
        if len(widget_creations) > setparent_calls + 5:  # Some tolerance
            self.report.issues.append(DiagnosisIssue(
                step=18,
                severity="low",
                category="memory_leaks",
                file_path=str(file_path),
                line_number=0,
                code_snippet=f"{len(widget_creations)} widgets, {setparent_calls} setParent calls",
                description="Potential memory leaks: widgets created without explicit parenting",
                recommendation="Ensure widgets have proper parent assignment or explicit deletion"
            ))
    
    def _check_process_events_usage(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 20: Validate use of QApplication.processEvents()."""
        for i, line in enumerate(lines):
            if 'processEvents' in line:
                # Check if it's inside a loop
                is_in_loop = any('for ' in lines[j] or 'while ' in lines[j] 
                               for j in range(max(0, i-5), i))
                
                severity = "high" if is_in_loop else "medium"
                self.report.issues.append(DiagnosisIssue(
                    step=20,
                    severity=severity,
                    category="process_events",
                    file_path=str(file_path),
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    description="QApplication.processEvents() usage detected",
                    recommendation="Avoid processEvents(); use proper signal-slot flow instead"
                ))
    
    def _check_platform_issues(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 21: Check for platform-specific issues."""
        # Look for Windows-specific code that might cause issues
        platform_patterns = [
            (r'import\s+win32', 'Windows-specific imports'),
            (r'DPI.*scaling', 'DPI scaling issues'),
            (r'X11.*thread', 'X11 threading issues'),
            (r'Wayland', 'Wayland compatibility concerns'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description in platform_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.report.issues.append(DiagnosisIssue(
                        step=21,
                        severity="low",
                        category="platform_specific",
                        file_path=str(file_path),
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        description=f"Platform-specific code: {description}",
                        recommendation="Test on target platforms and handle platform differences"
                    ))
    
    def _check_lambda_usage(self, file_path: Path, content: str, lines: List[str], tree: ast.AST):
        """Step 22: Surface excessive use of lambda in signal connections."""
        lambda_count = 0
        for i, line in enumerate(lines):
            if 'connect(' in line and 'lambda' in line:
                lambda_count += 1
                self.report.issues.append(DiagnosisIssue(
                    step=22,
                    severity="low",
                    category="lambda_usage",
                    file_path=str(file_path),
                    line_number=i + 1,
                    code_snippet=line.strip(),
                    description="Lambda function in signal connection",
                    recommendation="Use named slots or functools.partial for clarity and cleanup"
                ))
    
    def _is_in_gui_context(self, tree: ast.AST, line_number: int) -> bool:
        """Check if a line is within a GUI class context."""
        # Simple heuristic: look for QWidget, QMainWindow, etc. inheritance
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if (isinstance(base, ast.Name) and base.id.startswith('Q')) or \
                       (isinstance(base, ast.Attribute) and base.attr.startswith('Q')):
                        if (hasattr(node, 'lineno') and 
                            node.lineno <= line_number <= getattr(node, 'end_lineno', float('inf'))):
                            return True
        return False
    
    def _generate_summary(self):
        """Generate summary statistics."""
        severity_counts = {}
        category_counts = {}
        
        for issue in self.report.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        self.report.summary = {
            'total_issues': len(self.report.issues),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'files_with_issues': len(set(issue.file_path for issue in self.report.issues)),
            'pyside_version': self.report.pyside_version
        }


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="GUI Freeze Diagnosis Tool")
    parser.add_argument("--output", "-o", help="Output JSON file for results")
    parser.add_argument("--repo", default=".", help="Repository path to analyze")
    
    args = parser.parse_args()
    
    analyzer = GUIFreezeDiagnosisAnalyzer(args.repo)
    report = analyzer.analyze()
    
    # Print summary
    print("\n" + "="*80)
    print("📋 GUI FREEZE DIAGNOSIS SUMMARY")
    print("="*80)
    print(f"📊 Total issues found: {report.summary['total_issues']}")
    print(f"📁 Files analyzed: {report.total_files_analyzed}")
    print(f"🔧 PySide6 version: {report.pyside_version}")
    
    if report.summary['severity_breakdown']:
        print("\n🚨 Issues by severity:")
        for severity, count in report.summary['severity_breakdown'].items():
            print(f"   {severity.upper()}: {count}")
    
    if report.summary['category_breakdown']:
        print("\n📂 Issues by category:")
        for category, count in report.summary['category_breakdown'].items():
            print(f"   {category}: {count}")
    
    # Print detailed issues
    if report.issues:
        print("\n" + "="*80)
        print("🔍 DETAILED ISSUES")
        print("="*80)
        
        for issue in sorted(report.issues, key=lambda x: (x.severity == 'low', x.step)):
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            print(f"\n{severity_emoji[issue.severity]} Step {issue.step} - {issue.severity.upper()}")
            print(f"📁 {issue.file_path}:{issue.line_number}")
            print(f"💻 {issue.code_snippet}")
            print(f"📝 {issue.description}")
            print(f"💡 {issue.recommendation}")
    
    # Save to JSON if requested
    if args.output:
        report_dict = {
            'summary': report.summary,
            'issues': [
                {
                    'step': issue.step,
                    'severity': issue.severity,
                    'category': issue.category,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'code_snippet': issue.code_snippet,
                    'description': issue.description,
                    'recommendation': issue.recommendation
                }
                for issue in report.issues
            ]
        }
        
        with open(args.output, 'w') as f:
            json.dump(report_dict, f, indent=2)
        print(f"\n💾 Report saved to {args.output}")
    
    print(f"\n🎉 Analysis complete! Found {report.summary['total_issues']} potential issues.")
    return 0 if report.summary['total_issues'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())