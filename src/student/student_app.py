"""
Student Application for FocusClass
Main GUI and functionality for the student
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
    QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QPainter

# Import our modules
sys.path.append(str(Path(__file__).parent.parent))
from common.database_manager import DatabaseManager
from common.network_manager import NetworkManager
from common.screen_capture import StudentScreenShare
from common.focus_manager import FocusManager, LightweightFocusManager
from common.utils import (
    setup_logging, parse_qr_code_data, get_local_ip, 
    format_duration, EventEmitter
)
from common.config import *


class ConnectionDialog(QDialog):
    """Dialog for connecting to teacher"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Teacher")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Connection methods
        methods_group = QGroupBox("Connection Method")
        methods_layout = QVBoxLayout(methods_group)
        
        # Manual connection
        manual_group = QGroupBox("Manual Connection")
        manual_layout = QFormLayout(manual_group)
        
        self.teacher_ip_edit = QLineEdit()
        self.teacher_ip_edit.setPlaceholderText("192.168.1.100")
        manual_layout.addRow("Teacher IP:", self.teacher_ip_edit)
        
        self.session_code_edit = QLineEdit()
        self.session_code_edit.setPlaceholderText("ABC12345")
        manual_layout.addRow("Session Code:", self.session_code_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        manual_layout.addRow("Password:", self.password_edit)
        
        self.student_name_edit = QLineEdit()
        self.student_name_edit.setPlaceholderText("Your name")
        manual_layout.addRow("Your Name:", self.student_name_edit)
        
        methods_layout.addWidget(manual_group)
        
        # QR Code section
        qr_group = QGroupBox("QR Code")
        qr_layout = QVBoxLayout(qr_group)
        
        qr_info = QLabel("Scan QR code from teacher's screen or enter code manually:")
        qr_layout.addWidget(qr_info)
        
        self.qr_code_edit = QLineEdit()
        self.qr_code_edit.setPlaceholderText("Paste QR code data here")
        qr_layout.addWidget(self.qr_code_edit)
        
        parse_qr_btn = QPushButton("Parse QR Code")
        parse_qr_btn.clicked.connect(self.parse_qr_code)
        qr_layout.addWidget(parse_qr_btn)
        
        methods_layout.addWidget(qr_group)
        
        # Discovery section
        discovery_group = QGroupBox("Auto-Discovery")
        discovery_layout = QVBoxLayout(discovery_group)
        
        discover_btn = QPushButton("Discover Teachers on Network")
        discover_btn.clicked.connect(self.discover_teachers)
        discovery_layout.addWidget(discover_btn)
        
        self.discovery_list = QComboBox()
        self.discovery_list.setEnabled(False)
        discovery_layout.addWidget(self.discovery_list)
        
        methods_layout.addWidget(discovery_group)
        
        layout.addWidget(methods_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def parse_qr_code(self):
        """Parse QR code data"""
        qr_text = self.qr_code_edit.text().strip()
        if not qr_text:
            return
        
        try:
            qr_data = parse_qr_code_data(qr_text)
            if qr_data:
                self.teacher_ip_edit.setText(qr_data.get("teacher_ip", ""))
                self.session_code_edit.setText(qr_data.get("session_code", ""))
                self.password_edit.setText(qr_data.get("password", ""))
                
                QMessageBox.information(self, "Success", "QR code parsed successfully!")
            else:
                QMessageBox.warning(self, "Error", "Invalid QR code format")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse QR code: {str(e)}")
    
    def discover_teachers(self):
        """Discover teachers on network"""
        # TODO: Implement network discovery
        QMessageBox.information(self, "Info", "Network discovery not yet implemented")
    
    def get_connection_data(self) -> Dict[str, str]:
        """Get connection data from dialog"""
        return {
            "teacher_ip": self.teacher_ip_edit.text().strip(),
            "session_code": self.session_code_edit.text().strip(),
            "password": self.password_edit.text().strip(),
            "student_name": self.student_name_edit.text().strip()
        }


class VideoDisplayWidget(QWidget):
    """Widget to display teacher's screen stream"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_frame = None
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: black;")
        
        # Connection status
        self.connected = False
        self.connection_text = "Not connected to teacher"
        
        # Instructions
        self.instruction_text = "Waiting for teacher to start screen sharing..."
    def set_frame(self, frame_data):
        """Set video frame to display"""
        self.current_frame = frame_data
        self.connected = True
        self.update()
    
    def set_connection_status(self, connected: bool, text: str = ""):
        """Set connection status"""
        self.connected = connected
        if text:
            self.connection_text = text
        self.update()
    
    def paintEvent(self, event):
        """Paint the video frame or status message"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if self.current_frame and self.connected:
            # Draw video frame
            painter.drawPixmap(self.rect(), self.current_frame)
            
            # Show frame info overlay
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 10))
            frame_info = f"Frame: {self.current_frame.width()}x{self.current_frame.height()}"
            painter.drawText(10, 20, frame_info)
        else:
            # Draw status text
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 14))
            
            if not self.connected:
                text = self.connection_text
            else:
                text = self.instruction_text
            
            painter.drawText(self.rect(), Qt.AlignCenter, text)


class StudentControlWidget(QWidget):
    """Widget for student controls and status"""
    
    disconnect_requested = pyqtSignal()
    screen_share_response = pyqtSignal(bool)  # True = approve, False = deny
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.focus_mode_active = False
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Connection status
        status_group = QGroupBox("Connection Status")
        status_layout = QGridLayout(status_group)
        
        status_layout.addWidget(QLabel("Teacher:"), 0, 0)
        self.teacher_label = QLabel("Not connected")
        status_layout.addWidget(self.teacher_label, 0, 1)
        
        status_layout.addWidget(QLabel("Session:"), 1, 0)
        self.session_label = QLabel("None")
        status_layout.addWidget(self.session_label, 1, 1)
        
        status_layout.addWidget(QLabel("Focus Mode:"), 2, 0)
        self.focus_status_label = QLabel("Disabled")
        status_layout.addWidget(self.focus_status_label, 2, 1)
        
        layout.addWidget(status_group)
        
        # Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        self.disconnect_btn.setEnabled(False)
        controls_layout.addWidget(self.disconnect_btn)
        
        # Settings
        self.fullscreen_checkbox = QCheckBox("Fullscreen Mode")
        self.fullscreen_checkbox.toggled.connect(self.toggle_fullscreen)
        controls_layout.addWidget(self.fullscreen_checkbox)
        
        self.auto_approve_checkbox = QCheckBox("Auto-approve screen requests")
        controls_layout.addWidget(self.auto_approve_checkbox)
        
        layout.addWidget(controls_group)
        
        # Status messages
        messages_group = QGroupBox("Messages")
        messages_layout = QVBoxLayout(messages_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        messages_layout.addWidget(self.status_text)
        
        layout.addWidget(messages_group)
        
        layout.addStretch()
    
    def set_connection_status(self, connected: bool, teacher_ip: str = "", session_code: str = ""):
        """Update connection status"""
        self.connected = connected
        
        if connected:
            self.teacher_label.setText(teacher_ip)
            self.session_label.setText(session_code)
            self.disconnect_btn.setEnabled(True)
        else:
            self.teacher_label.setText("Not connected")
            self.session_label.setText("None")
            self.disconnect_btn.setEnabled(False)
    
    def set_focus_mode(self, active: bool):
        """Update focus mode status"""
        self.focus_mode_active = active
        self.focus_status_label.setText("Enabled" if active else "Disabled")
        
        if active:
            self.focus_status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.focus_status_label.setStyleSheet("")
    
    def add_status_message(self, message: str):
        """Add a status message"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.End)
        self.status_text.setTextCursor(cursor)
    
    def toggle_fullscreen(self, enabled: bool):
        """Toggle fullscreen mode"""
        if enabled:
            self.parent().showFullScreen()
        else:
            self.parent().showNormal()


class ScreenShareRequestDialog(QDialog):
    """Dialog for screen share requests"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Screen Share Request")
        self.setModal(True)
        self.resize(300, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        message = QLabel("The teacher has requested to view your screen.")
        message.setWordWrap(True)
        layout.addWidget(message)
        
        warning = QLabel("This will share your entire screen with the teacher.")
        warning.setStyleSheet("color: red;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.Yes | QDialogButtonBox.No
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)


class StudentMainWindow(QMainWindow):
    """Main window for student application"""
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logging("INFO", "logs/student.log")
        
        # Initialize components
        self.network_manager = NetworkManager(is_teacher=False)
        self.screen_share = StudentScreenShare(self.handle_screen_share_request)
        self.focus_manager = None  # Will be initialized based on privileges
        
        # Connection state
        self.connected = False
        self.teacher_ip = ""
        self.session_code = ""
        self.student_name = ""
        
        # Focus mode state
        self.focus_mode_active = False
        self.restrictions_active = False
        self.keystroke_monitoring = False
        self.battery_monitoring = False
        
        # Monitoring data
        self.keystroke_count = 0
        self.last_keystroke_report = time.time()
        self.last_battery_report = time.time()
        
        # Enhanced restrictions
        self.no_tab_switching = False
        self.no_window_minimize = False
        self.no_external_apps = False
        
        # Setup UI
        self.setup_ui()
        self.setup_timers()
        self.setup_signals()
        
        # Initialize focus manager
        self.init_focus_manager()
        
        # Show connection dialog
        self.show_connection_dialog()
        
        self.logger.info("Student application initialized")
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("FocusClass Student")
        self.setMinimumSize(800, 600)
        self.resize(1024, 768)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Video display (main area)
        self.video_display = VideoDisplayWidget(self)
        main_layout.addWidget(self.video_display, 3)
        
        # Control panel (right side)
        self.control_panel = StudentControlWidget(self)
        self.control_panel.setMaximumWidth(300)
        main_layout.addWidget(self.control_panel)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.connection_status_label = QLabel("Disconnected")
        self.focus_status_label = QLabel("Focus Mode: Off")
        
        self.status_bar.addWidget(self.connection_status_label)
        self.status_bar.addPermanentWidget(self.focus_status_label)
    
    def setup_timers(self):
        """Setup periodic timers"""
        # Heartbeat timer
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        
        # Connection check timer
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(5000)  # Check every 5 seconds
    
    def setup_signals(self):
        """Setup signal connections"""
        # Control panel signals
        self.control_panel.disconnect_requested.connect(self.disconnect_from_teacher)
        self.control_panel.screen_share_response.connect(self.respond_to_screen_request)
        
        # Network manager signals
        self.setup_network_handlers()
        
        # Global keystroke monitoring (if enabled)
        self.keystroke_timer = QTimer()
        self.keystroke_timer.timeout.connect(self.report_keystroke_data)
        
        # Battery monitoring timer
        self.battery_timer = QTimer()
        self.battery_timer.timeout.connect(self.report_battery_status)
        
        # System monitoring timer
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.report_system_info)
    
    def setup_network_handlers(self):
        """Setup network event handlers"""
        # Message handlers
        self.network_manager.register_message_handler("auth_success", self.handle_auth_success)
        self.network_manager.register_message_handler("auth_failed", self.handle_auth_failed)
        self.network_manager.register_message_handler("focus_mode", self.handle_focus_mode)
        self.network_manager.register_message_handler("restriction_change", self.handle_restriction_change)
        self.network_manager.register_message_handler("force_disconnect", self.handle_force_disconnect)
        self.network_manager.register_message_handler("screen_request", self.handle_screen_request)
        self.network_manager.register_message_handler("teacher_stream", self.handle_teacher_stream)
        # Additional handlers to support basic (non-WebRTC) screen sharing and welcome/session info
        # These were missing and caused "No handler for message type: welcome/screen_frame" warnings
        self.network_manager.register_message_handler("welcome", self.handle_welcome)
        self.network_manager.register_message_handler("screen_sharing", self.handle_screen_sharing)
        self.network_manager.register_message_handler("screen_frame", self.handle_screen_frame)
        
        # Connection handlers
        self.network_manager.register_connection_handler("disconnection", self.handle_disconnection)
    
    async def handle_welcome(self, client_id: str, data: Dict[str, Any]):
        """Handle welcome message from teacher - update session info UI"""
        try:
            # Teacher may send session information in welcome payload
            session_code = data.get("session_code") or data.get("session") or self.session_code
            teacher_ip = data.get("teacher_ip") or getattr(self, 'teacher_ip', '')
            password = data.get("password")
            
            if session_code:
                self.session_code = session_code
                self.control_panel.set_connection_status(self.connected, teacher_ip, session_code)
            
            # If the teacher sent a password or ip, update internal fields
            if teacher_ip:
                self.teacher_ip = teacher_ip
            if password:
                self.control_panel.add_status_message("Received session details from teacher")
            
        except Exception as e:
            self.logger.error(f"Error handling welcome message: {e}")
    
    async def handle_screen_sharing(self, client_id: str, data: Dict[str, Any]):
        """Handle screen sharing control messages (start/stop)"""
        try:
            action = data.get("action", "start")
            if action == "start":
                self.video_display.instruction_text = "Teacher started screen sharing..."
                self.video_display.set_connection_status(True, "Receiving screen")
                self.control_panel.add_status_message("Teacher started screen sharing")
            else:
                # Stop sharing
                self.video_display.set_connection_status(False, "Teacher stopped sharing")
                self.video_display.current_frame = None
                self.video_display.update()
                self.control_panel.add_status_message("Teacher stopped screen sharing")
        
        except Exception as e:
            self.logger.error(f"Error handling screen_sharing message: {e}")
    
    async def handle_screen_frame(self, client_id: str, data: Dict[str, Any]):
        """Handle incoming screen frame (base64-encoded PNG/JPEG) and display it"""
        try:
            frame_b64 = data.get("frame") or data.get("image") or data.get("frame_data")
            if not frame_b64:
                self.logger.warning("Screen frame received with no data")
                return
            
            import base64
            from PyQt5.QtGui import QPixmap
            
            # Debug log frame info
            frame_size = data.get("width", "unknown")
            frame_height = data.get("height", "unknown")
            frame_format = data.get("format", "unknown")
            self.logger.debug(f"Received frame: {frame_size}x{frame_height}, format: {frame_format}")
            
            # Some implementations send frame as bytes, some as base64 string
            if isinstance(frame_b64, (bytes, bytearray)):
                raw = bytes(frame_b64)
            else:
                raw = base64.b64decode(frame_b64)
            
            pixmap = QPixmap()
            if pixmap.loadFromData(raw):
                # Scale pixmap to fit widget while preserving aspect ratio
                scaled = pixmap.scaled(self.video_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.video_display.set_frame(scaled)
                self.logger.debug(f"Frame displayed successfully: {scaled.width()}x{scaled.height()}")
            else:
                self.logger.error("Failed to load pixmap from incoming frame data")
                # Try to save raw data for debugging
                with open("debug_frame.bin", "wb") as f:
                    f.write(raw[:1000])  # Save first 1000 bytes for inspection
        
        except Exception as e:
            self.logger.error(f"Error handling screen_frame: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def init_keystroke_monitoring(self):
        """Initialize keystroke monitoring"""
        try:
            # Install global keystroke hook if on Windows
            if sys.platform == "win32":
                import win32gui
                import win32con
                
                # This is a simplified keystroke counter
                # In a real implementation, you'd use a proper global hook
                self.logger.info("Keystroke monitoring initialized")
            else:
                self.logger.warning("Keystroke monitoring not supported on this platform")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize keystroke monitoring: {e}")
    
    def init_battery_monitoring(self):
        """Initialize battery monitoring"""
        try:
            import psutil
            
            # Check if battery is available
            battery = psutil.sensors_battery()
            if battery:
                self.logger.info("Battery monitoring initialized")
            else:
                self.logger.warning("No battery detected (desktop system?)")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize battery monitoring: {e}")
    
    def init_system_monitoring(self):
        """Initialize system monitoring"""
        try:
            import psutil
            self.logger.info("System monitoring initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize system monitoring: {e}")
    
    def init_focus_manager(self):
        """Initialize focus manager based on privileges"""
        try:
            from common.focus_manager import FocusManager, LightweightFocusManager, is_admin
            
            if is_admin():
                self.focus_manager = FocusManager(self.handle_violation)
                self.logger.info("Full focus manager initialized (admin privileges)")
            else:
                self.focus_manager = LightweightFocusManager(self.handle_violation)
                self.logger.info("Lightweight focus manager initialized (limited privileges)")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize focus manager: {e}")
            # Fallback to no focus manager
            self.focus_manager = None
    
    def show_connection_dialog(self):
        """Show connection dialog"""
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            connection_data = dialog.get_connection_data()
            self.connect_to_teacher(connection_data)
        else:
            # User cancelled - exit application
            self.close()
    
    def connect_to_teacher(self, connection_data: Dict[str, str]):
        """Connect to teacher"""
        asyncio.create_task(self._connect_to_teacher_async(connection_data))
    
    async def _connect_to_teacher_async(self, connection_data: Dict[str, str]):
        """Async connection to teacher"""
        try:
            teacher_ip = connection_data["teacher_ip"]
            session_code = connection_data["session_code"]
            password = connection_data["password"]
            student_name = connection_data["student_name"]
            
            if not all([teacher_ip, session_code, password, student_name]):
                QMessageBox.warning(self, "Error", "Please fill in all fields")
                return
            
            # Show connecting status
            self.control_panel.add_status_message("Connecting to teacher...")
            self.video_display.set_connection_status(False, "Connecting...")
            
            # Attempt connection
            success = await self.network_manager.connect_to_teacher(
                teacher_ip, session_code, password, student_name
            )
            
            if success:
                self.teacher_ip = teacher_ip
                self.session_code = session_code
                self.student_name = student_name
                
                self.control_panel.add_status_message("Connected successfully!")
                self.logger.info(f"Connected to teacher at {teacher_ip}")
            else:
                QMessageBox.critical(self, "Connection Failed", 
                                   "Failed to connect to teacher. Please check your connection details.")
                self.show_connection_dialog()
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            self.show_connection_dialog()
    
    async def handle_auth_success(self, client_id: str, data: Dict[str, Any]):
        """Handle successful authentication"""
        self.connected = True
        
        # Update UI
        self.control_panel.set_connection_status(True, self.teacher_ip, self.session_code)
        self.video_display.set_connection_status(True, "Connected to teacher")
        self.connection_status_label.setText(f"Connected to {self.teacher_ip}")
        
        # Start heartbeat
        self.heartbeat_timer.start(10000)  # Every 10 seconds
        
        # Handle enhanced configuration
        self.keystroke_monitoring = data.get("keystroke_monitoring", False)
        self.battery_monitoring = data.get("battery_monitoring", False)
        
        restrictions = data.get("restrictions", {})
        self.no_tab_switching = restrictions.get("no_tab_switching", False)
        self.no_window_minimize = restrictions.get("no_window_minimize", False)
        self.no_external_apps = restrictions.get("no_external_apps", False)
        
        # Start monitoring if enabled
        if self.keystroke_monitoring:
            self.keystroke_timer.start(30000)  # Report every 30 seconds
            self.control_panel.add_status_message("Keystroke monitoring enabled")
        
        if self.battery_monitoring:
            self.battery_timer.start(60000)  # Report every minute
            self.control_panel.add_status_message("Battery monitoring enabled")
        
        # Start system monitoring
        self.system_timer.start(120000)  # Report every 2 minutes
        
        # Handle focus mode if enabled
        focus_mode = data.get("focus_mode", False)
        if focus_mode:
            await self.enable_focus_mode()
        
        self.control_panel.add_status_message("Authentication successful")
        self.logger.info("Authentication successful")
    
    async def handle_restriction_change(self, client_id: str, data: Dict[str, Any]):
        """Handle restriction level changes"""
        try:
            level = data.get("level", "normal")
            status = data.get("status", "connected")
            
            if level == "high":
                self.restrictions_active = True
                # Apply enhanced restrictions
                if self.focus_manager:
                    await self.focus_manager.enable_focus_mode(["FocusClass Student"])
                
                self.control_panel.add_status_message("High restriction mode activated")
                
                # Disable certain UI elements
                self.control_panel.fullscreen_checkbox.setEnabled(False)
                
            else:
                self.restrictions_active = False
                self.control_panel.fullscreen_checkbox.setEnabled(True)
                self.control_panel.add_status_message("Normal restriction mode")
            
            self.logger.info(f"Restriction level changed to: {level}")
            
        except Exception as e:
            self.logger.error(f"Error handling restriction change: {e}")
    
    async def handle_force_disconnect(self, client_id: str, data: Dict[str, Any]):
        """Handle forced disconnection by teacher"""
        try:
            reason = data.get("reason", "Disconnected by teacher")
            
            QMessageBox.warning(self, "Disconnected", f"You have been disconnected: {reason}")
            
            # Cleanup and close
            await self.cleanup()
            self.close()
            
        except Exception as e:
            self.logger.error(f"Error handling force disconnect: {e}")
    
    def report_keystroke_data(self):
        """Report keystroke monitoring data"""
        if self.connected and self.keystroke_monitoring:
            asyncio.create_task(self._report_keystroke_data_async())
    
    async def _report_keystroke_data_async(self):
        """Async keystroke data reporting"""
        try:
            # In a real implementation, this would count actual keystrokes
            # For now, we'll simulate keystroke counting
            current_time = time.time()
            time_diff = current_time - self.last_keystroke_report
            
            # Simulate keystroke count (random for demo)
            import random
            new_keystrokes = random.randint(50, 200)  # Simulated keystrokes
            self.keystroke_count += new_keystrokes
            
            await self.network_manager._send_message("teacher", "keystroke_data", {
                "count": self.keystroke_count,
                "session_keystrokes": new_keystrokes,
                "timestamp": current_time
            })
            
            self.last_keystroke_report = current_time
            
        except Exception as e:
            self.logger.error(f"Error reporting keystroke data: {e}")
    
    def report_battery_status(self):
        """Report battery status"""
        if self.connected and self.battery_monitoring:
            asyncio.create_task(self._report_battery_status_async())
    
    async def _report_battery_status_async(self):
        """Async battery status reporting"""
        try:
            import psutil
            
            battery = psutil.sensors_battery()
            if battery:
                battery_level = int(battery.percent)
                is_charging = battery.power_plugged
            else:
                # Desktop system - simulate full battery
                battery_level = 100
                is_charging = True
            
            await self.network_manager._send_message("teacher", "battery_status", {
                "level": battery_level,
                "charging": is_charging,
                "timestamp": time.time()
            })
            
            # Check for low battery and report as malicious activity
            if battery_level < 20 and not is_charging:
                await self.network_manager._send_message("teacher", "malicious_activity", {
                    "type": "low_battery_warning",
                    "description": f"Battery critically low: {battery_level}% (not charging)",
                    "severity": "high",
                    "timestamp": time.time()
                })
            
            self.last_battery_report = time.time()
            
        except Exception as e:
            self.logger.error(f"Error reporting battery status: {e}")
    
    def report_system_info(self):
        """Report system information"""
        if self.connected:
            asyncio.create_task(self._report_system_info_async())
    
    async def _report_system_info_async(self):
        """Async system info reporting"""
        try:
            import psutil
            
            # Get system stats
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # Get running processes count
            process_count = len(psutil.pids())
            
            system_info = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "process_count": process_count,
                "timestamp": time.time()
            }
            
            await self.network_manager._send_message("teacher", "system_info", system_info)
            
            # Check for suspicious activity
            if cpu_usage > 80:
                await self.network_manager._send_message("teacher", "malicious_activity", {
                    "type": "high_cpu_usage",
                    "description": f"Unusual CPU usage detected: {cpu_usage}%",
                    "severity": "medium",
                    "timestamp": time.time()
                })
            
            if memory_usage > 85:
                await self.network_manager._send_message("teacher", "malicious_activity", {
                    "type": "high_memory_usage",
                    "description": f"High memory usage detected: {memory_usage}%",
                    "severity": "medium",
                    "timestamp": time.time()
                })
            
        except Exception as e:
            self.logger.error(f"Error reporting system info: {e}")
    
    async def handle_auth_failed(self, client_id: str, data: Dict[str, Any]):
        """Handle authentication failure"""
        reason = data.get("reason", "Unknown error")
        QMessageBox.critical(self, "Authentication Failed", f"Authentication failed: {reason}")
        self.show_connection_dialog()
    
    async def handle_focus_mode(self, client_id: str, data: Dict[str, Any]):
        """Handle focus mode change"""
        enabled = data.get("enabled", False)
        
        if enabled:
            await self.enable_focus_mode()
        else:
            await self.disable_focus_mode()
    
    async def enable_focus_mode(self):
        """Enable focus mode"""
        try:
            if not self.focus_mode_active:
                allowed_windows = [STUDENT_WINDOW_TITLE, "FocusClass Student"]
                success = await self.focus_manager.enable_focus_mode(allowed_windows)
                
                if success:
                    self.focus_mode_active = True
                    self.control_panel.set_focus_mode(True)
                    self.focus_status_label.setText("Focus Mode: ON")
                    self.focus_status_label.setStyleSheet("color: red; font-weight: bold;")
                    
                    self.control_panel.add_status_message("Focus mode enabled")
                    self.logger.info("Focus mode enabled")
                else:
                    self.control_panel.add_status_message("Failed to enable focus mode")
                    
        except Exception as e:
            self.logger.error(f"Error enabling focus mode: {e}")
    
    async def disable_focus_mode(self):
        """Disable focus mode"""
        try:
            if self.focus_mode_active:
                success = await self.focus_manager.disable_focus_mode()
                
                if success:
                    self.focus_mode_active = False
                    self.control_panel.set_focus_mode(False)
                    self.focus_status_label.setText("Focus Mode: OFF")
                    self.focus_status_label.setStyleSheet("")
                    
                    self.control_panel.add_status_message("Focus mode disabled")
                    self.logger.info("Focus mode disabled")
                    
        except Exception as e:
            self.logger.error(f"Error disabling focus mode: {e}")
    
    async def handle_violation(self, violation_data: Dict[str, Any]):
        """Handle focus mode violation"""
        try:
            # Send violation to teacher
            await self.network_manager._send_message("teacher", "violation", violation_data)
            
            violation_type = violation_data.get("type", "unknown")
            self.control_panel.add_status_message(f"Violation detected: {violation_type}")
            
            self.logger.warning(f"Focus violation: {violation_type}")
            
        except Exception as e:
            self.logger.error(f"Error handling violation: {e}")
    
    async def handle_screen_request(self, client_id: str, data: Dict[str, Any]):
        """Handle screen share request from teacher"""
        try:
            # Check auto-approve setting
            if self.control_panel.auto_approve_checkbox.isChecked():
                await self.respond_to_screen_request(True)
            else:
                # Show approval dialog
                dialog = ScreenShareRequestDialog(self)
                response = dialog.exec_()
                approved = response == QDialog.Accepted
                
                await self.respond_to_screen_request(approved)
                
        except Exception as e:
            self.logger.error(f"Error handling screen request: {e}")
    
    async def respond_to_screen_request(self, approved: bool):
        """Respond to screen share request"""
        try:
            if approved:
                # Start screen sharing
                result = await self.screen_share.handle_share_request({})
                
                if result["success"]:
                    self.control_panel.add_status_message("Screen sharing started")
                    # TODO: Send screen share stream to teacher
                else:
                    self.control_panel.add_status_message("Failed to start screen sharing")
            else:
                self.control_panel.add_status_message("Screen share request denied")
            
            # Send response to teacher
            await self.network_manager._send_message("teacher", "screen_response", {
                "approved": approved
            })
            
        except Exception as e:
            self.logger.error(f"Error responding to screen request: {e}")
    
    async def handle_screen_share_request(self, request_data: Dict[str, Any]) -> bool:
        """Handle screen share approval request"""
        # This is called by the screen share component
        if self.control_panel.auto_approve_checkbox.isChecked():
            return True
        
        # Show dialog for manual approval
        dialog = ScreenShareRequestDialog(self)
        response = dialog.exec_()
        return response == QDialog.Accepted
    
    async def handle_teacher_stream(self, client_id: str, data: Dict[str, Any]):
        """Handle teacher's screen stream"""
        # TODO: Handle incoming video stream from teacher
        pass
    
    async def handle_disconnection(self, client_id: str):
        """Handle disconnection from teacher"""
        self.connected = False
        
        # Stop focus mode
        if self.focus_mode_active:
            await self.disable_focus_mode()
        
        # Stop screen sharing
        await self.screen_share.stop_sharing()
        
        # Stop timers
        self.heartbeat_timer.stop()
        
        # Update UI
        self.control_panel.set_connection_status(False)
        self.video_display.set_connection_status(False, "Disconnected from teacher")
        self.connection_status_label.setText("Disconnected")
        
        self.control_panel.add_status_message("Disconnected from teacher")
        self.logger.info("Disconnected from teacher")
        
        # Show reconnection dialog
        QMessageBox.information(self, "Disconnected", "You have been disconnected from the teacher.")
        self.show_connection_dialog()
    
    def disconnect_from_teacher(self):
        """Disconnect from teacher"""
        asyncio.create_task(self._disconnect_async())
    
    async def _disconnect_async(self):
        """Async disconnection"""
        try:
            await self.network_manager.disconnect_client()
            await self.handle_disconnection("teacher")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
    
    def send_heartbeat(self):
        """Send heartbeat to teacher"""
        if self.connected:
            asyncio.create_task(self._send_heartbeat_async())
    
    async def _send_heartbeat_async(self):
        """Async heartbeat with enhanced data"""
        try:
            heartbeat_data = {
                "timestamp": time.time(),
                "focus_active": self.focus_mode_active,
                "restrictions_active": self.restrictions_active
            }
            
            # Add system stats if available
            try:
                import psutil
                heartbeat_data["system_stats"] = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "battery_level": getattr(psutil.sensors_battery(), 'percent', 100) if psutil.sensors_battery() else 100
                }
            except:
                pass
            
            await self.network_manager._send_message("teacher", "heartbeat", heartbeat_data)
            
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
    
    def check_connection(self):
        """Check connection status"""
        # TODO: Implement connection health check
        pass
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.connected:
            reply = QMessageBox.question(
                self, "Exit Application",
                "You are still connected to the teacher. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Cleanup
        asyncio.create_task(self.cleanup())
        event.accept()
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop all monitoring timers
            self.keystroke_timer.stop()
            self.battery_timer.stop()
            self.system_timer.stop()
            
            if self.connected:
                await self.network_manager.disconnect_client()
            
            if self.focus_manager:
                await self.focus_manager.cleanup()
            
            await self.screen_share.stop_sharing()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Setup async event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create main window
    window = StudentMainWindow()
    window.show()
    
    # Run the application
    with loop:
        await loop.run_forever()


if __name__ == "__main__":
    if sys.platform == "win32":
        # Windows specific setup
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("FocusClass Student")
    
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)