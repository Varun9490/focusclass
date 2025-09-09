"""
Advanced Teacher Application for FocusClass
Enhanced version with complete monitoring and management features
"""

import sys
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import qasync

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QTabWidget, QGroupBox, QGridLayout, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QProgressBar, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QScrollArea, QMenuBar, QMenu, QAction,
    QSystemTrayIcon, QFileDialog, QStatusBar, QSlider
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor

# Import our modules
sys.path.append(str(Path(__file__).parent.parent))
from common.database_manager import DatabaseManager
from common.network_manager import NetworkManager, generate_session_code, generate_session_password
from common.screen_capture import ScreenCapture, AdaptiveQuality
from common.utils import (
    setup_logging, create_qr_code, image_to_base64, 
    get_local_ip, format_duration, format_bytes, EventEmitter
)
from common.config import *
from teacher.teacher_app import TeacherMainWindow


class AdvancedTeacherApp(TeacherMainWindow):
    """Enhanced teacher application with advanced monitoring features"""
    
    window_closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusClass Teacher - Advanced Dashboard")
        self.enhance_ui()
        
    def enhance_ui(self):
        """Enhance the UI with advanced features"""
        # Add advanced styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #007ACC;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 25px;
            }
            QTextEdit, QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                font-weight: bold;
                color: #495057;
            }
            QStatusBar {
                background-color: #343a40;
                color: white;
                border: none;
            }
            QStatusBar QLabel {
                color: white;
                padding: 4px 8px;
            }
        """)
        
        # Add menu bar
        self.add_menu_bar()
        
        # Add toolbar
        self.add_toolbar()
        
    def add_menu_bar(self):
        """Add enhanced menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #343a40;
                color: white;
                border: none;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #495057;
            }
            QMenu {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 8px 12px;
                color: #343a40;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
            }
        """)
        
        # Session menu
        session_menu = menubar.addMenu('Session')
        
        new_session_action = QAction('New Session', self)
        new_session_action.setShortcut('Ctrl+N')
        new_session_action.triggered.connect(self.start_session)
        session_menu.addAction(new_session_action)
        
        end_session_action = QAction('End Session', self)
        end_session_action.setShortcut('Ctrl+E')
        end_session_action.triggered.connect(self.stop_session)
        session_menu.addAction(end_session_action)
        
        session_menu.addSeparator()
        
        export_action = QAction('Export Report', self)
        export_action.setShortcut('Ctrl+S')
        export_action.triggered.connect(self.export_activity_report)
        session_menu.addAction(export_action)
        
        # Students menu
        students_menu = menubar.addMenu('Students')
        
        admit_action = QAction('Admit Student', self)
        admit_action.triggered.connect(self.admit_student_dialog)
        students_menu.addAction(admit_action)
        
        remove_all_action = QAction('Remove All Students', self)
        remove_all_action.triggered.connect(self.remove_all_students)
        students_menu.addAction(remove_all_action)
        
        students_menu.addSeparator()
        
        broadcast_action = QAction('Broadcast Message', self)
        broadcast_action.triggered.connect(self.broadcast_message_dialog)
        students_menu.addAction(broadcast_action)
        
        # Monitoring menu
        monitoring_menu = menubar.addMenu('Monitoring')
        
        self.keystroke_action = QAction('Enable Keystroke Monitoring', self)
        self.keystroke_action.setCheckable(True)
        self.keystroke_action.setChecked(self.keystroke_monitoring)
        self.keystroke_action.triggered.connect(self.toggle_keystroke_monitoring)
        monitoring_menu.addAction(self.keystroke_action)
        
        self.battery_action = QAction('Enable Battery Monitoring', self)
        self.battery_action.setCheckable(True)
        self.battery_action.setChecked(self.charging_monitoring)
        self.battery_action.triggered.connect(self.toggle_battery_monitoring)
        monitoring_menu.addAction(self.battery_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About FocusClass', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def add_toolbar(self):
        """Add toolbar with quick actions"""
        toolbar = self.addToolBar('Quick Actions')
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 1px solid #dee2e6;
                spacing: 8px;
                padding: 8px;
            }
            QToolButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #005A9E;
            }
        """)
        
        # Quick start session
        quick_start = QAction('🚀 Quick Start', self)
        quick_start.triggered.connect(self.quick_start_session)
        toolbar.addAction(quick_start)
        
        toolbar.addSeparator()
        
        # Emergency stop
        emergency_stop = QAction('🛑 Emergency Stop', self)
        emergency_stop.triggered.connect(self.emergency_stop)
        toolbar.addAction(emergency_stop)
        
        toolbar.addSeparator()
        
        # Focus all
        focus_all = QAction('🎯 Focus All', self)
        focus_all.triggered.connect(self.focus_all_students)
        toolbar.addAction(focus_all)
        
        # Release all
        release_all = QAction('🔓 Release All', self)
        release_all.triggered.connect(self.release_all_students)
        toolbar.addAction(release_all)
        
    def admit_student_dialog(self):
        """Show dialog to manually admit a student"""
        QMessageBox.information(self, "Admit Student", 
                              "Students can join by scanning the QR code or entering session details manually.")
    
    def remove_all_students(self):
        """Remove all students from session"""
        if not self.connected_students:
            QMessageBox.information(self, "No Students", "No students are currently connected.")
            return
            
        reply = QMessageBox.question(self, "Remove All Students",
                                   f"Are you sure you want to remove all {len(self.connected_students)} students?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            asyncio.create_task(self._remove_all_students_async())
    
    async def _remove_all_students_async(self):
        """Async remove all students"""
        try:
            for client_id in list(self.connected_students.keys()):
                await self._remove_student_async(client_id)
        except Exception as e:
            self.logger.error(f"Error removing all students: {e}")
    
    def broadcast_message_dialog(self):
        """Show dialog to broadcast message to all students"""
        if not self.connected_students:
            QMessageBox.information(self, "No Students", "No students are currently connected.")
            return
            
        from PyQt5.QtWidgets import QInputDialog
        message, ok = QInputDialog.getText(self, "Broadcast Message", 
                                         "Enter message to send to all students:")
        
        if ok and message:
            asyncio.create_task(self._broadcast_message_async(message))
    
    async def _broadcast_message_async(self, message: str):
        """Async broadcast message"""
        try:
            await self.network_manager.broadcast_message("teacher_message", {
                "message": message,
                "timestamp": time.time()
            })
            self.logger.info(f"Broadcasted message: {message}")
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}")
    
    def toggle_keystroke_monitoring(self, enabled: bool):
        """Toggle keystroke monitoring"""
        self.keystroke_monitoring = enabled
        self.keystroke_action.setText(
            "Disable Keystroke Monitoring" if enabled else "Enable Keystroke Monitoring"
        )
        
        # Broadcast to all students
        asyncio.create_task(self.network_manager.broadcast_message("monitoring_change", {
            "keystroke_monitoring": enabled
        }))
        
        self.logger.info(f"Keystroke monitoring {'enabled' if enabled else 'disabled'}")
    
    def toggle_battery_monitoring(self, enabled: bool):
        """Toggle battery monitoring"""
        self.charging_monitoring = enabled
        self.battery_action.setText(
            "Disable Battery Monitoring" if enabled else "Enable Battery Monitoring"
        )
        
        # Broadcast to all students
        asyncio.create_task(self.network_manager.broadcast_message("monitoring_change", {
            "battery_monitoring": enabled
        }))
        
        self.logger.info(f"Battery monitoring {'enabled' if enabled else 'disabled'}")
    
    def quick_start_session(self):
        """Quick start a session with default settings"""
        if not self.session_active:
            self.start_session()
        else:
            QMessageBox.information(self, "Session Active", "A session is already running.")
    
    def emergency_stop(self):
        """Emergency stop all activities"""
        reply = QMessageBox.warning(self, "Emergency Stop",
                                   "This will immediately stop the session and disconnect all students.\n"
                                   "Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            asyncio.create_task(self._emergency_stop_async())
    
    async def _emergency_stop_async(self):
        """Async emergency stop"""
        try:
            # Broadcast emergency stop to all students
            await self.network_manager.broadcast_message("emergency_stop", {
                "reason": "Emergency stop activated by teacher"
            })
            
            # Stop session
            await self._stop_session_async()
            
            self.logger.warning("Emergency stop executed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
    
    def focus_all_students(self):
        """Enable focus mode for all students"""
        if not self.connected_students:
            QMessageBox.information(self, "No Students", "No students are currently connected.")
            return
            
        asyncio.create_task(self._focus_all_students_async())
    
    async def _focus_all_students_async(self):
        """Async focus all students"""
        try:
            await self.network_manager.broadcast_message("force_focus", {
                "enabled": True,
                "level": "high"
            })
            
            # Update focus mode checkbox
            self.focus_mode_checkbox.setChecked(True)
            self.focus_mode_active = True
            
            self.logger.info("Enabled focus mode for all students")
            
        except Exception as e:
            self.logger.error(f"Error focusing all students: {e}")
    
    def release_all_students(self):
        """Disable focus mode for all students"""
        if not self.connected_students:
            QMessageBox.information(self, "No Students", "No students are currently connected.")
            return
            
        asyncio.create_task(self._release_all_students_async())
    
    async def _release_all_students_async(self):
        """Async release all students"""
        try:
            await self.network_manager.broadcast_message("force_focus", {
                "enabled": False,
                "level": "normal"
            })
            
            # Update focus mode checkbox
            self.focus_mode_checkbox.setChecked(False)
            self.focus_mode_active = False
            
            self.logger.info("Disabled focus mode for all students")
            
        except Exception as e:
            self.logger.error(f"Error releasing all students: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        <h2>FocusClass Professional</h2>
        <p><b>Version:</b> {APP_VERSION}</p>
        <p><b>Advanced Teacher Dashboard</b></p>
        
        <h3>Features:</h3>
        <ul>
            <li>Real-time screen sharing</li>
            <li>Student monitoring & restrictions</li>
            <li>Keystroke & battery monitoring</li>
            <li>Malicious activity detection</li>
            <li>Student management controls</li>
            <li>Session reporting & analytics</li>
        </ul>
        
        <p><b>© 2025 FocusClass Team</b></p>
        """
        
        QMessageBox.about(self, "About FocusClass", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.session_active:
            reply = QMessageBox.question(
                self, "Close Application",
                "Session is active. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Cleanup
        if self.session_active:
            asyncio.create_task(self._stop_session_async())
        
        # Emit signal for launcher
        self.window_closed.emit()
        event.accept()


async def main():
    """Main entry point for standalone execution"""
    app = QApplication(sys.argv)
    
    # Setup async event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create main window
    window = AdvancedTeacherApp()
    window.show()
    
    # Run the application
    with loop:
        await loop.run_forever()


if __name__ == "__main__":
    if sys.platform == "win32":
        # Windows specific setup
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("FocusClass Advanced Teacher")
    
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)