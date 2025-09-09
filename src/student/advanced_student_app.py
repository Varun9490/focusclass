
"""
Advanced Student Application for FocusClass
Enhanced version with security monitoring and advanced restrictions
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
    QLabel, QPushButton, QTextEdit, QLineEdit, QDialog, QMessageBox,
    QGroupBox, QGridLayout, QFormLayout, QDialogButtonBox,
    QProgressBar, QStatusBar, QCheckBox, QComboBox, QPushButton,
    QFrame, QScrollArea, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QPainter

# Import our modules
sys.path.append(str(Path(__file__).parent.parent))
from student.student_app import StudentMainWindow
from common.database_manager import DatabaseManager
from common.network_manager import NetworkManager
from common.screen_capture import StudentScreenShare
from common.focus_manager import FocusManager, LightweightFocusManager
from common.utils import (
    setup_logging, parse_qr_code_data, get_local_ip, 
    format_duration, EventEmitter
)
from common.config import *


class AdvancedStudentApp(StudentMainWindow):
    """Advanced student application with enhanced security monitoring"""
    
    window_closed = pyqtSignal()
    
    def __init__(self):
        """Initialize advanced student application"""
        super().__init__()
        
        # Enhanced security features
        self.secure_mode_active = False
        self.violation_threshold = 5
        
        # Security monitoring components
        self.security_monitor = None
        self.restriction_manager = None
        
        # Ensure focus_manager is properly initialized
        if not hasattr(self, 'focus_manager') or self.focus_manager is None:
            from common.focus_manager import FocusManager, LightweightFocusManager
            try:
                self.focus_manager = FocusManager(self.handle_security_violation)
            except Exception as e:
                self.logger.warning(f"Could not initialize FocusManager, using lightweight version: {e}")
                self.focus_manager = LightweightFocusManager(self.handle_security_violation)
        
        # Enhanced UI setup
        self.setup_enhanced_ui()
        
        self.logger.info("Advanced student application initialized")
    
    def setup_enhanced_ui(self):
        """Setup enhanced UI elements"""
        # Add security status panel
        security_group = QGroupBox("Security Status")
        security_layout = QGridLayout(security_group)
        
        security_layout.addWidget(QLabel("Secure Mode:"), 0, 0)
        self.security_status = QLabel("Inactive")
        self.security_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        security_layout.addWidget(self.security_status, 0, 1)
        
        # Emergency help button
        self.emergency_btn = QPushButton("Emergency Help")
        self.emergency_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.emergency_btn.clicked.connect(self.request_emergency_help)
        security_layout.addWidget(self.emergency_btn, 1, 0, 1, 2)
        
        # Add to control panel
        self.control_panel.layout().addWidget(security_group)
    
    async def enable_secure_mode(self, level: str = "normal"):
        """Enable secure mode with enhanced restrictions"""
        try:
            self.secure_mode_active = True
            self.security_status.setText("Active")
            self.security_status.setStyleSheet("color: #28a745; font-weight: bold;")
            
            # Enable restrictions through focus manager if available
            if hasattr(self, 'focus_manager') and self.focus_manager:
                await self.focus_manager.enable_focus_mode(["FocusClass Student"])
            
            # Update UI
            if hasattr(self, 'control_panel') and self.control_panel:
                self.control_panel.add_status_message("Secure mode enabled - Enhanced restrictions active")
            
            self.logger.info(f"Secure mode enabled: {level}")
            
        except Exception as e:
            self.logger.error(f"Error enabling secure mode: {e}")
    
    async def disable_secure_mode(self):
        """Disable secure mode"""
        try:
            self.secure_mode_active = False
            self.security_status.setText("Inactive")
            self.security_status.setStyleSheet("color: #dc3545; font-weight: bold;")
            
            # Disable restrictions if available
            if hasattr(self, 'restriction_manager') and self.restriction_manager:
                await self.restriction_manager.disable_restrictions()
            
            # Stop security monitoring if available
            if hasattr(self, 'security_monitor') and self.security_monitor:
                await self.security_monitor.stop_monitoring()
            
            # Update UI
            if hasattr(self, 'control_panel') and self.control_panel:
                self.control_panel.add_status_message("Secure mode disabled")
            
            self.logger.info("Secure mode disabled")
            
        except Exception as e:
            self.logger.error(f"Error disabling secure mode: {e}")
    
    async def handle_security_violation(self, violation_data: Dict[str, Any]):
        """Handle security violations"""
        try:
            # Send to teacher
            await self.network_manager._send_message("teacher", "malicious_activity", violation_data)
            
            # Update UI
            violation_type = violation_data.get("type", "unknown")
            severity = violation_data.get("severity", "medium")
            
            self.control_panel.add_status_message(
                f"Security alert: {violation_type} ({severity.upper()})"
            )
            
            # Check violation threshold
            if self.security_monitor.violation_count >= self.violation_threshold:
                await self._handle_violation_threshold_exceeded()
            
        except Exception as e:
            self.logger.error(f"Error handling security violation: {e}")
    
    async def _handle_violation_threshold_exceeded(self):
        """Handle when violation threshold is exceeded"""
        try:
            # Notify teacher of excessive violations
            await self.network_manager._send_message("teacher", "malicious_activity", {
                "type": "violation_threshold_exceeded",
                "description": f"Student has exceeded violation threshold ({self.violation_threshold} violations)",
                "severity": "high",
                "timestamp": time.time(),
                "total_violations": self.security_monitor.violation_count
            })
            
            # Show warning to student
            QMessageBox.warning(
                self, "Security Warning", 
                "Multiple security violations detected.\n"
                "Your teacher has been notified.\n\n"
                "Please follow the classroom guidelines."
            )
            
        except Exception as e:
            self.logger.error(f"Error handling violation threshold: {e}")
    
    def request_emergency_help(self):
        """Request emergency help from teacher"""
        asyncio.create_task(self._request_emergency_help_async())
    
    async def _request_emergency_help_async(self):
        """Async emergency help request"""
        try:
            from PyQt5.QtWidgets import QInputDialog
            
            reason, ok = QInputDialog.getText(
                self, "Emergency Help", 
                "Please describe your issue:"
            )
            
            if ok and reason:
                await self.network_manager._send_message("teacher", "emergency_help", {
                    "student_name": self.student_name,
                    "reason": reason,
                    "timestamp": time.time(),
                    "urgent": True
                })
                
                QMessageBox.information(
                    self, "Help Request Sent", 
                    "Your help request has been sent to the teacher."
                )
                
                self.control_panel.add_status_message("Emergency help requested")
                self.logger.info(f"Emergency help requested: {reason}")
                
        except Exception as e:
            self.logger.error(f"Error requesting emergency help: {e}")
    
    async def handle_force_focus(self, client_id: str, data: Dict[str, Any]):
        """Handle forced focus mode from teacher"""
        try:
            enabled = data.get("enabled", False)
            level = data.get("level", "normal")
            
            if enabled:
                await self.enable_secure_mode(level)
                await self.enable_focus_mode()
            else:
                await self.disable_secure_mode()
                await self.disable_focus_mode()
                
        except Exception as e:
            self.logger.error(f"Error handling force focus: {e}")
    
    async def handle_emergency_stop(self, client_id: str, data: Dict[str, Any]):
        """Handle emergency stop from teacher"""
        try:
            reason = data.get("reason", "Emergency stop")
            
            # Disable all restrictions immediately
            await self.disable_secure_mode()
            await self.disable_focus_mode()
            
            # Show notification
            QMessageBox.warning(
                self, "Emergency Stop", 
                f"Emergency stop activated by teacher:\n{reason}"
            )
            
            # Disconnect after a delay
            QTimer.singleShot(3000, self.close)
            
        except Exception as e:
            self.logger.error(f"Error handling emergency stop: {e}")
    
    async def handle_teacher_message(self, client_id: str, data: Dict[str, Any]):
        """Handle message from teacher"""
        try:
            message = data.get("message", "")
            timestamp = data.get("timestamp", time.time())
            
            # Show message to student
            QMessageBox.information(
                self, "Message from Teacher", 
                f"Teacher says:\n\n{message}"
            )
            
            # Add to status messages
            self.control_panel.add_status_message(f"Teacher: {message}")
            
        except Exception as e:
            self.logger.error(f"Error handling teacher message: {e}")
    
    def setup_network_handlers(self):
        """Setup enhanced network event handlers"""
        super().setup_network_handlers()
        
        # Add additional handlers
        self.network_manager.register_message_handler("force_focus", self.handle_force_focus)
        self.network_manager.register_message_handler("emergency_stop", self.handle_emergency_stop)
        self.network_manager.register_message_handler("teacher_message", self.handle_teacher_message)
        self.network_manager.register_message_handler("monitoring_change", self.handle_monitoring_change)
    
    async def handle_monitoring_change(self, client_id: str, data: Dict[str, Any]):
        """Handle monitoring configuration changes"""
        try:
            keystroke_monitoring = data.get("keystroke_monitoring")
            battery_monitoring = data.get("battery_monitoring")
            
            if keystroke_monitoring is not None:
                self.keystroke_monitoring = keystroke_monitoring
                if keystroke_monitoring:
                    self.keystroke_timer.start(30000)
                    self.control_panel.add_status_message("Keystroke monitoring enabled")
                else:
                    self.keystroke_timer.stop()
                    self.control_panel.add_status_message("Keystroke monitoring disabled")
            
            if battery_monitoring is not None:
                self.battery_monitoring = battery_monitoring
                if battery_monitoring:
                    self.battery_timer.start(60000)
                    self.control_panel.add_status_message("Battery monitoring enabled")
                else:
                    self.battery_timer.stop()
                    self.control_panel.add_status_message("Battery monitoring disabled")
            
        except Exception as e:
            self.logger.error(f"Error handling monitoring change: {e}")
    
    def closeEvent(self, event):
        """Handle window close event with enhanced cleanup"""
        if self.secure_mode_active:
            reply = QMessageBox.question(
                self, "Exit Secure Mode",
                "You are in secure mode. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Enhanced cleanup
        asyncio.create_task(self._enhanced_cleanup())
        
        # Emit signal for launcher
        self.window_closed.emit()
        event.accept()
    
    async def _enhanced_cleanup(self):
        """Enhanced cleanup with security components"""
        try:
            # Stop security monitoring
            if hasattr(self, 'security_monitor'):
                await self.security_monitor.stop_monitoring()
            
            # Disable restrictions
            if hasattr(self, 'restriction_manager'):
                await self.restriction_manager.disable_restrictions()
            
            # Standard cleanup
            await self.cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during enhanced cleanup: {e}")


async def main():
    """Main entry point for standalone execution"""
    app = QApplication(sys.argv)
    
    # Setup async event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create main window
    window = AdvancedStudentApp()
    window.show()
    
    # Run the application
    with loop:
        await loop.run_forever()


if __name__ == "__main__":
    if sys.platform == "win32":
        # Windows specific setup
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("FocusClass Advanced Student")
    
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)