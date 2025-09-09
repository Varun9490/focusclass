"""
Teacher Application for FocusClass
Main GUI and functionality for the teacher
"""

import sys
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from io import BytesIO
import qasync

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QTabWidget, QGroupBox, QGridLayout, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QProgressBar, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QScrollArea, QMenuBar, QMenu, QAction,
    QSystemTrayIcon, QFileDialog, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor

# Try to import QWebEngineView for HTML interface
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtWebChannel import QWebChannel
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False
    print("Warning: QWebEngineView not available. Using traditional PyQt5 interface.")

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
from .performance_monitor import PerformanceMonitor


class TeacherMainWindow(QMainWindow):
    """Main window for teacher application"""
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logging("INFO", "logs/teacher.log")
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.network_manager = NetworkManager(is_teacher=True)
        self.screen_capture = ScreenCapture()
        
        self.performance_monitor = PerformanceMonitor()
        
        # Session state
        self.session_id = None
        self.session_active = False
        self.screen_sharing_active = False
        self.focus_mode_active = False
        
        # Student management
        self.connected_students = {}
        self.malicious_activities = {}
        
        # Enhanced monitoring
        self.keystroke_monitoring = True
        self.charging_monitoring = True
        self.battery_threshold = 20  # Alert when battery below 20%
        
        # Setup UI
        self.setup_ui()
        self.setup_timers()
        self.setup_network_handlers()
        
        # Toast notification list
        self.active_toasts = []
        
        self.logger.info("Teacher application initialized")
    
    def schedule_async_task(self, coro):
        """Schedule an async task safely"""
        try:
            # Get the current event loop
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                # Use ensure_future for better compatibility with qasync
                asyncio.ensure_future(coro)
            else:
                # Try alternative approach
                asyncio.create_task(coro)
        except RuntimeError as e:
            # Fallback: try to schedule using QTimer for Qt thread safety
            self.logger.warning(f"Asyncio scheduling failed: {e}, using QTimer fallback")
            from PyQt5.QtCore import QTimer
            timer = QTimer()
            timer.singleShot(0, lambda: asyncio.ensure_future(coro))
    def show_toast(self, message: str, toast_type: str = "info"):
        """Show modern toast notification"""
        from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
        
        # Create toast widget
        toast = QLabel(message, self)
        toast.setWordWrap(True)
        toast.setMaximumWidth(400)
        
        # Style based on type
        if toast_type == "success":
            bg_color = "rgba(76, 175, 80, 0.95)"
            text_color = "white"
            icon = "✅"
        elif toast_type == "error":
            bg_color = "rgba(244, 67, 54, 0.95)"
            text_color = "white"
            icon = "❌"
        elif toast_type == "warning":
            bg_color = "rgba(255, 152, 0, 0.95)"
            text_color = "white"
            icon = "⚠️"
        else:  # info
            bg_color = "rgba(33, 150, 243, 0.95)"
            text_color = "white"
            icon = "ℹ️"
        
        toast.setText(f"{icon} {message}")
        toast.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)
        
        # Position toast (stack them)
        toast.adjustSize()
        x = self.width() - toast.width() - 20
        y = 20 + len(self.active_toasts) * (toast.height() + 10)
        toast.move(x, y)
        toast.show()
        
        # Add to active toasts
        self.active_toasts.append(toast)
        
        # Animation
        opacity_effect = QGraphicsOpacityEffect()
        toast.setGraphicsEffect(opacity_effect)
        
        # Slide in from right
        toast.move(self.width(), y)
        
        # Animate position and opacity
        from PyQt5.QtCore import QPropertyAnimation, QParallelAnimationGroup, QPoint
        
        position_anim = QPropertyAnimation(toast, b"pos")
        position_anim.setDuration(300)
        position_anim.setStartValue(toast.pos())
        position_anim.setEndValue(QPoint(x, y))
        position_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(0)
        opacity_anim.setEndValue(1)
        
        # Group animations
        anim_group = QParallelAnimationGroup()
        anim_group.addAnimation(position_anim)
        anim_group.addAnimation(opacity_anim)
        anim_group.start()
        
        # Auto hide after 3 seconds
        QTimer.singleShot(3000, lambda: self.hide_toast(toast, opacity_effect))
    
    def hide_toast(self, toast, opacity_effect):
        """Hide toast with fade out animation"""
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
        
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
        
        fade_out = QPropertyAnimation(opacity_effect, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(toast.deleteLater)
        fade_out.start()
        
        # Reposition remaining toasts
        self.reposition_toasts()
    
    def reposition_toasts(self):
        """Reposition remaining toasts after one is removed"""
        for i, toast in enumerate(self.active_toasts):
            new_y = 20 + i * (toast.height() + 10)
            
            from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint
            anim = QPropertyAnimation(toast, b"pos")
            anim.setDuration(200)
            anim.setStartValue(toast.pos())
            anim.setEndValue(QPoint(toast.pos().x(), new_y))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
    
    def start_basic_screen_sharing_timer(self):
        """Start timer for basic screen sharing without WebRTC"""
        if not hasattr(self, 'basic_sharing_timer'):
            self.basic_sharing_timer = QTimer()
            self.basic_sharing_timer.timeout.connect(self.capture_and_send_frame)
        
        # Send frames every 1 second for better performance  
        self.basic_sharing_timer.start(1000)
        self.logger.info("Basic screen sharing timer started (1fps)")
    
    def stop_basic_screen_sharing_timer(self):
        """Stop basic screen sharing timer"""
        if hasattr(self, 'basic_sharing_timer'):
            self.basic_sharing_timer.stop()
            self.logger.info("Basic screen sharing timer stopped")
    
    def capture_and_send_frame(self):
        """Capture and send frame for basic screen sharing"""
        try:
            if not self.screen_sharing_active:
                return
                
            # Capture screenshot using MSS directly for better performance
            import mss
            import base64
            import io
            from PIL import Image
            
            with mss.mss() as sct:
                # Get primary monitor (monitor 1 in MSS, 0 is all monitors)
                monitor = sct.monitors[1]
                
                # Capture screen
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image and resize for better transmission
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Resize to reduce bandwidth (scale to 75% for medium quality)
                new_width = int(img.width * 0.75)
                new_height = int(img.height * 0.75)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to JPEG bytes
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=70, optimize=True)
                frame_data = buffer.getvalue()
                
                # Convert to base64 for transmission
                frame_b64 = base64.b64encode(frame_data).decode('utf-8')
                
                # Send to all connected students
                self.schedule_async_task(self.network_manager.broadcast_message("screen_frame", {
                    "frame": frame_b64,
                    "timestamp": time.time(),
                    "format": "jpeg",
                    "width": new_width,
                    "height": new_height
                }))
                
                # Update UI with frame info
                frame_size_kb = len(frame_data) / 1024
                self.logger.debug(f"Sent frame: {new_width}x{new_height}, {frame_size_kb:.1f}KB")
                
        except Exception as e:
            self.logger.error(f"Error capturing and sending frame: {e}")
            # Don't stop sharing on single frame error, just log it
    
    def setup_network_handlers(self):
        """Setup network message and connection handlers"""
        # Register message handlers
        self.network_manager.register_message_handler("authenticate", self.handle_student_authentication)
        self.network_manager.register_message_handler("violation", self.handle_violation)
        self.network_manager.register_message_handler("heartbeat", self.handle_heartbeat)
        self.network_manager.register_message_handler("keystroke_data", self.handle_keystroke_data)
        self.network_manager.register_message_handler("battery_status", self.handle_battery_status)
        self.network_manager.register_message_handler("system_info", self.handle_system_info)
        self.network_manager.register_message_handler("malicious_activity", self.handle_malicious_activity)
        
        # Register connection handlers
        self.network_manager.register_connection_handler("connection", self.handle_student_connection)
        self.network_manager.register_connection_handler("disconnection", self.handle_student_disconnection)
    
    async def handle_student_authentication(self, client_id: str, data: Dict[str, Any]):
        """Handle student authentication"""
        try:
            student_name = data.get("student_name")
            password = data.get("password")
            session_code = data.get("session_code")
            
            self.logger.info(f"Authentication attempt from {client_id}: {student_name}")
            
            # Get client IP address
            client_ip = self.network_manager.get_client_ip(client_id)
            
            # Add to database
            if self.session_id:
                student_id = await self.db_manager.add_student(
                    self.session_id, student_name, client_ip
                )
            
            # Add to connected students with real IP
            self.connected_students[client_id] = {
                "name": student_name,
                "ip_address": client_ip,
                "connected_at": time.time(),
                "violations": 0,
                "keystrokes": 0,
                "battery_level": 100,
                "is_charging": True,
                "focus_mode": False,
                "status": "connected"
            }
            
            # Update UI
            self.refresh_student_list()
            self.students_label.setText(f"Students: {len(self.connected_students)}")
            
            self.show_toast(f"✅ {student_name} connected from {client_ip}", "success")
            self.logger.info(f"Student authenticated: {student_name} ({client_ip})")
                
        except Exception as e:
            self.logger.error(f"Error in student authentication: {e}")
            
    async def handle_student_connection(self, client_id: str, websocket):
        """Handle new student connection"""
        try:
            client_ip = self.network_manager.get_client_ip(client_id)
            self.logger.info(f"New student connection: {client_id} from {client_ip}")
            
        except Exception as e:
            self.logger.error(f"Error handling student connection: {e}")
            
    async def handle_student_disconnection(self, client_id: str):
        """Handle student disconnection"""
        try:
            if client_id in self.connected_students:
                student_info = self.connected_students[client_id]
                student_name = student_info.get("name", "Unknown")
                student_ip = student_info.get("ip_address", "unknown")
                
                # Remove from connected students
                del self.connected_students[client_id]
                
                # Update UI
                self.refresh_student_list()
                self.students_label.setText(f"Students: {len(self.connected_students)}")
                
                # Log to violation log
                disconnect_time = time.strftime("%H:%M:%S")
                self.violation_log.append(f"[{disconnect_time}] 🔌 {student_name} ({student_ip}) disconnected")
                
                # Show notification
                self.show_toast(f"⚠️ {student_name} disconnected from {student_ip}", "warning")
                self.logger.info(f"Student disconnected: {student_name} ({student_ip})")
                
        except Exception as e:
            self.logger.error(f"Error handling student disconnection: {e}")
    
    async def handle_violation(self, client_id: str, data: Dict[str, Any]):
        """Handle focus mode violation"""
        try:
            if client_id in self.connected_students:
                student_info = self.connected_students[client_id]
                student_name = student_info.get("name", "Unknown")
                violation_type = data.get("type", "unknown")
                
                # Increment violation count
                student_info["violations"] = student_info.get("violations", 0) + 1
                
                # Log violation
                violation_time = time.strftime("%H:%M:%S")
                self.violation_log.append(f"[{violation_time}] ⚠️ {student_name}: {violation_type}")
                
                # Update UI
                self.refresh_student_list()
                
                self.logger.warning(f"Violation from {student_name}: {violation_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling violation: {e}")
    
    async def handle_heartbeat(self, client_id: str, data: Dict[str, Any]):
        """Handle student heartbeat"""
        try:
            if client_id in self.connected_students:
                self.connected_students[client_id]["last_heartbeat"] = time.time()
                
        except Exception as e:
            self.logger.error(f"Error handling heartbeat: {e}")
    
    async def handle_keystroke_data(self, client_id: str, data: Dict[str, Any]):
        """Handle keystroke monitoring data"""
        try:
            if client_id in self.connected_students:
                keystroke_count = data.get("count", 0)
                self.connected_students[client_id]["keystrokes"] = keystroke_count
                self.refresh_student_list()
                
        except Exception as e:
            self.logger.error(f"Error handling keystroke data: {e}")
    
    async def handle_battery_status(self, client_id: str, data: Dict[str, Any]):
        """Handle battery status update"""
        try:
            if client_id in self.connected_students:
                battery_level = data.get("level", 100)
                is_charging = data.get("charging", True)
                
                self.connected_students[client_id]["battery_level"] = battery_level
                self.connected_students[client_id]["is_charging"] = is_charging
                
                self.refresh_student_list()
                
        except Exception as e:
            self.logger.error(f"Error handling battery status: {e}")
    
    async def handle_system_info(self, client_id: str, data: Dict[str, Any]):
        """Handle system information update"""
        try:
            if client_id in self.connected_students:
                cpu_usage = data.get("cpu_usage", 0)
                memory_usage = data.get("memory_usage", 0)
                
                self.connected_students[client_id]["cpu_usage"] = cpu_usage
                self.connected_students[client_id]["memory_usage"] = memory_usage
                
        except Exception as e:
            self.logger.error(f"Error handling system info: {e}")
    
    async def handle_malicious_activity(self, client_id: str, data: Dict[str, Any]):
        """Handle malicious activity report"""
        try:
            if client_id in self.connected_students:
                student_name = self.connected_students[client_id].get("name", "Unknown")
                activity_type = data.get("type", "unknown")
                description = data.get("description", "")
                severity = data.get("severity", "low")
                
                # Log to malicious activities
                activity_time = time.strftime("%H:%M:%S")
                self.malicious_list.append(f"[{activity_time}] {student_name}: {description}")
                
                # Show warning toast for high severity
                if severity == "high":
                    self.show_toast(f"🚨 {student_name}: {description}", "error")
                
                self.logger.warning(f"Malicious activity from {student_name}: {description}")
                
        except Exception as e:
            self.logger.error(f"Error handling malicious activity: {e}")
    
    def show_toast(self, message: str, toast_type: str = "info"):
        """Show modern toast notification"""
        from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
        
        # Create toast widget
        toast = QLabel(message, self)
        toast.setWordWrap(True)
        toast.setMaximumWidth(400)
        
        # Style based on type
        if toast_type == "success":
            bg_color = "rgba(76, 175, 80, 0.95)"
            text_color = "white"
            icon = "✅"
        elif toast_type == "error":
            bg_color = "rgba(244, 67, 54, 0.95)"
            text_color = "white"
            icon = "❌"
        elif toast_type == "warning":
            bg_color = "rgba(255, 152, 0, 0.95)"
            text_color = "white"
            icon = "⚠️"
        else:  # info
            bg_color = "rgba(33, 150, 243, 0.95)"
            text_color = "white"
            icon = "ℹ️"
        
        toast.setText(f"{icon} {message}")
        toast.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)
        
        # Position toast (stack them)
        toast.adjustSize()
        x = self.width() - toast.width() - 20
        y = 20 + len(self.active_toasts) * (toast.height() + 10)
        toast.move(x, y)
        toast.show()
        
        # Add to active toasts
        self.active_toasts.append(toast)
        
        # Animation
        opacity_effect = QGraphicsOpacityEffect()
        toast.setGraphicsEffect(opacity_effect)
        
        # Slide in from right
        toast.move(self.width(), y)
        
        # Animate position and opacity
        from PyQt5.QtCore import QPropertyAnimation, QParallelAnimationGroup, QPoint
        
        position_anim = QPropertyAnimation(toast, b"pos")
        position_anim.setDuration(300)
        position_anim.setStartValue(toast.pos())
        position_anim.setEndValue(QPoint(x, y))
        position_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(0)
        opacity_anim.setEndValue(1)
        
        # Group animations
        anim_group = QParallelAnimationGroup()
        anim_group.addAnimation(position_anim)
        anim_group.addAnimation(opacity_anim)
        anim_group.start()
        
        # Auto hide after 3 seconds
        QTimer.singleShot(3000, lambda: self.hide_toast(toast, opacity_effect))
    
    def hide_toast(self, toast, opacity_effect):
        """Hide toast with fade out animation"""
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
        
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
        
        fade_out = QPropertyAnimation(opacity_effect, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(toast.deleteLater)
        fade_out.start()
        
        # Reposition remaining toasts
        self.reposition_toasts()
    
    def reposition_toasts(self):
        """Reposition remaining toasts after one is removed"""
        for i, toast in enumerate(self.active_toasts):
            new_y = 20 + i * (toast.height() + 10)
            
            from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint
            anim = QPropertyAnimation(toast, b"pos")
            anim.setDuration(200)
            anim.setStartValue(toast.pos())
            anim.setEndValue(QPoint(toast.pos().x(), new_y))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
    
    def start_basic_screen_sharing_timer(self):
        """Start timer for basic screen sharing without WebRTC"""
        if not hasattr(self, 'basic_sharing_timer'):
            self.basic_sharing_timer = QTimer()
            self.basic_sharing_timer.timeout.connect(self.capture_and_send_frame)
        
        # Send frames every 2 seconds for basic mode
        self.basic_sharing_timer.start(2000)
        self.logger.info("Basic screen sharing timer started")
    
    def stop_basic_screen_sharing_timer(self):
        """Stop basic screen sharing timer"""
        if hasattr(self, 'basic_sharing_timer'):
            self.basic_sharing_timer.stop()
            self.logger.info("Basic screen sharing timer stopped")
    
    def capture_and_send_frame(self):
        """Capture and send frame for basic screen sharing"""
        try:
            frame_data = self.screen_capture.capture_frame_data()
            if frame_data:
                # Convert to base64 for transmission
                import base64
                frame_b64 = base64.b64encode(frame_data).decode('utf-8')
                
                # Send to all connected students
                self.schedule_async_task(self.network_manager.broadcast_message("screen_frame", {
                    "frame_data": frame_b64,
                    "timestamp": time.time(),
                    "format": "jpeg"
                }))
                
        except Exception as e:
            self.logger.error(f"Error capturing and sending frame: {e}")
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("FocusClass Teacher")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Session Controls
        left_panel = self.create_left_panel()
        # Right panel - Student List
        right_panel = self.create_right_panel()
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.students_label = QLabel("Students: 0")
        self.network_label = QLabel(f"IP: {get_local_ip()}")
        
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.students_label)
        self.status_bar.addPermanentWidget(self.network_label)
    
    def create_left_panel(self):
        """Create left control panel with improved layout"""
        left_panel = QWidget()
        left_panel.setMaximumWidth(450)  # Increased width
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        
        # Session info group with improved layout
        session_group = QGroupBox("📊 Session Information")
        session_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: rgba(255, 255, 255, 0.95);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #333;
            }
        """)
        
        session_layout = QVBoxLayout(session_group)
        session_layout.setSpacing(15)
        
        # Session details in separate cards
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setSpacing(10)
        
        # Session Code Card
        code_card = self.create_info_card("Session Code", "Not started", "#4CAF50")
        self.session_code_label = code_card.findChild(QLabel, "value_label")
        details_layout.addWidget(code_card)
        
        # Password Card
        pass_card = self.create_info_card("Password", "Not started", "#FF9800")
        self.password_label = pass_card.findChild(QLabel, "value_label")
        details_layout.addWidget(pass_card)
        
        # IP Address Card
        ip_card = self.create_info_card("Teacher IP", get_local_ip(), "#2196F3")
        self.ip_label = ip_card.findChild(QLabel, "value_label")
        details_layout.addWidget(ip_card)
        
        session_layout.addWidget(details_container)
        
        # QR Code in separate section with proper sizing
        qr_container = QWidget()
        qr_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px dashed #ccc;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setSpacing(10)
        
        qr_title = QLabel("🔗 Connection QR Code")
        qr_title.setFont(QFont("Arial", 12, QFont.Bold))
        qr_title.setAlignment(Qt.AlignCenter)
        qr_title.setStyleSheet("color: #666; border: none; padding: 0;")
        qr_layout.addWidget(qr_title)
        
        self.qr_label = QLabel("QR Code will appear here")
        self.qr_label.setMinimumSize(220, 220)  # Increased size
        self.qr_label.setMaximumSize(220, 220)
        self.qr_label.setStyleSheet("""
            QLabel {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                color: #999;
                font-size: 12px;
            }
        """)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setScaledContents(True)  # Scale QR code properly
        qr_layout.addWidget(self.qr_label, 0, Qt.AlignCenter)
        
        # Add Copy Session Details button
        copy_container = QWidget()
        copy_layout = QHBoxLayout(copy_container)
        copy_layout.setContentsMargins(0, 10, 0, 10)
        
        self.copy_session_btn = QPushButton("📋 Copy Session Details")
        self.copy_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.copy_session_btn.setEnabled(False)
        self.copy_session_btn.clicked.connect(self.copy_session_details)
        
        self.view_details_btn = QPushButton("📄 View Details")
        self.view_details_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a2d91;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.view_details_btn.setEnabled(False)
        self.view_details_btn.clicked.connect(self.view_session_details)
        
        copy_layout.addWidget(self.copy_session_btn)
        copy_layout.addWidget(self.view_details_btn)
        session_layout.addWidget(copy_container)
        
        left_layout.addWidget(session_group)
    
    def copy_session_details(self):
        """Copy session details to clipboard"""
        try:
            details = f"""FocusClass Session Details:
Session Code: {self.session_code_label.text()}
Password: {self.password_label.text()}
Teacher IP: {self.ip_label.text()}
WebSocket Port: 8765
HTTP Port: 8080

Share this information with students to join the session."""
            
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(details)
            
            self.show_toast("✅ Session details copied to clipboard!", "success")
            
        except Exception as e:
            self.logger.error(f"Error copying session details: {e}")
            self.show_toast("❌ Failed to copy session details", "error")
    
    def view_session_details(self):
        """Show detailed session information dialog"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Session Details")
            dialog.setModal(True)
            dialog.resize(450, 350)
            
            layout = QVBoxLayout(dialog)
            
            # Title
            title = QLabel("📊 FocusClass Session Information")
            title.setFont(QFont("Arial", 14, QFont.Bold))
            title.setStyleSheet("color: #4A90E2; margin-bottom: 10px;")
            layout.addWidget(title)
            
            # Session details in a text area
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(200)
            
            session_info = f"""Session Code: {self.session_code_label.text()}
                    Password: {self.password_label.text()}
                    Teacher IP: {self.ip_label.text()}
                    WebSocket Port: 8765
                    HTTP Port: 8080
                    Connected Students: {len(self.connected_students)}
                    Status: {'Active' if self.session_active else 'Inactive'}
                    Focus Mode: {'Enabled' if self.focus_mode_active else 'Disabled'}
                    Screen Sharing: {'Active' if self.screen_sharing_active else 'Inactive'}

                    Instructions for Students:
                    1. Open FocusClass Student application
                    2. Use manual connection with the above details
                    3. Or scan the QR code displayed in the main window"""
            
            details_text.setPlainText(session_info)
            details_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 10px;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                }
            """)
            layout.addWidget(details_text)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            copy_btn = QPushButton("📋 Copy All")
            copy_btn.clicked.connect(lambda: self.copy_text_to_clipboard(session_info))
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            
            button_layout.addWidget(copy_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"Error showing session details: {e}")
            self.show_toast("❌ Failed to show session details", "error")
    
    def copy_text_to_clipboard(self, text):
        """Copy given text to clipboard"""
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.show_toast("✅ Copied to clipboard!", "success")
        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")
            self.show_toast("❌ Failed to copy", "error")
        
        # Controls group
        controls_group = QGroupBox("🎮 Session Controls")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: rgba(255, 255, 255, 0.95);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #333;
            }
        """)
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(15)
        
        # Create controls section
        self.create_controls_section(controls_layout)
        
        # Add controls group to left layout
        left_layout.addWidget(controls_group)
        
        # Violation log
        violation_group = QGroupBox("⚠️ Violation Log")
        violation_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: rgba(255, 255, 255, 0.95);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #333;
            }
        """)
        violation_layout = QVBoxLayout(violation_group)
        
        log_header = QHBoxLayout()
        log_title = QLabel("Recent Violations")
        self.clear_log_btn = QPushButton("🗑️ Clear")
        self.clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.clear_log_btn.clicked.connect(self.clear_violation_log)
        
        log_header.addWidget(log_title)
        log_header.addStretch()
        log_header.addWidget(self.clear_log_btn)
        violation_layout.addLayout(log_header)
        
        self.violation_log = QTextEdit()
        self.violation_log.setReadOnly(True)
        self.violation_log.setMaximumHeight(150)
        self.violation_log.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        violation_layout.addWidget(self.violation_log)
        
        left_layout.addWidget(violation_group)
        left_layout.addStretch()
        
        return left_panel
    
    def create_info_card(self, title: str, value: str, color: str):
        """Create an information card widget"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.9);
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 10px;
                margin: 2px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(5)
        card_layout.setContentsMargins(10, 8, 10, 8)
        
        # Title label
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {color}; border: none; padding: 0;")
        card_layout.addWidget(title_label)
        
        # Value label
        value_label = QLabel(value)
        value_label.setFont(QFont("Courier", 12, QFont.Bold))
        value_label.setStyleSheet("color: #333; border: none; padding: 0;")
        value_label.setObjectName("value_label")  # For finding later
        value_label.setWordWrap(True)
        card_layout.addWidget(value_label)
        
        return card
    
    def create_controls_section(self, controls_layout):
        """Create the controls section of the UI"""
        # Session buttons
        session_btn_layout = QHBoxLayout()
        self.start_session_btn = QPushButton("🚀 Start Session")
        self.start_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.stop_session_btn = QPushButton("🛑 Stop Session")
        self.stop_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_session_btn.setEnabled(False)
        
        self.start_session_btn.clicked.connect(self.start_session)
        self.stop_session_btn.clicked.connect(self.stop_session)
        
        session_btn_layout.addWidget(self.start_session_btn)
        session_btn_layout.addWidget(self.stop_session_btn)
        controls_layout.addLayout(session_btn_layout)
        
        # Focus mode
        self.focus_mode_checkbox = QCheckBox("🎯 Enable Focus Mode")
        self.focus_mode_checkbox.setEnabled(False)
        self.focus_mode_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
            }
        """)
        self.focus_mode_checkbox.toggled.connect(self.toggle_focus_mode)
        controls_layout.addWidget(self.focus_mode_checkbox)
        
        # Screen sharing buttons
        screen_btn_layout = QHBoxLayout()
        self.start_sharing_btn = QPushButton("📺 Start Screen Sharing")
        self.start_sharing_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.stop_sharing_btn = QPushButton("🚫 Stop Screen Sharing")
        self.stop_sharing_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.start_sharing_btn.setEnabled(False)
        self.stop_sharing_btn.setEnabled(False)
        
        self.start_sharing_btn.clicked.connect(self.start_screen_sharing)
        self.stop_sharing_btn.clicked.connect(self.stop_screen_sharing)
        
        screen_btn_layout.addWidget(self.start_sharing_btn)
        screen_btn_layout.addWidget(self.stop_sharing_btn)
        controls_layout.addLayout(screen_btn_layout)
        
    def start_screen_sharing(self):
        """Start screen sharing"""
        self.schedule_async_task(self._start_screen_sharing_async())
    
    async def _start_screen_sharing_async(self):
        """Async screen sharing start"""
        try:
            if self.screen_sharing_active:
                self.show_toast("⚠️ Screen sharing already active", "warning")
                return
            
            # Start screen capture
            monitor_index = 0  # Primary monitor
            quality = "medium"  # Default quality
            
            success = self.screen_capture.start_capture(monitor_index, quality)
            
            if success:
                # Notify students about screen sharing start
                await self.network_manager.broadcast_message("screen_sharing", {
                    "action": "start",
                    "quality": quality,
                    "monitor": monitor_index
                })
                
                # Start sending frames
                self.start_basic_screen_sharing_timer()
                
                # Update UI
                self.screen_sharing_active = True
                self.start_sharing_btn.setEnabled(False)
                self.stop_sharing_btn.setEnabled(True)
                
                self.show_toast("📺 Screen sharing started", "success")
                self.logger.info("Screen sharing started")
                
            else:
                self.show_toast("❌ Failed to start screen sharing", "error")
                
        except Exception as e:
            self.logger.error(f"Error starting screen sharing: {e}")
            self.show_toast(f"❌ Error starting screen sharing: {str(e)}", "error")
    
    def stop_screen_sharing(self):
        """Stop screen sharing"""
        self.schedule_async_task(self._stop_screen_sharing_async())
    
    async def _stop_screen_sharing_async(self):
        """Async screen sharing stop"""
        try:
            if not self.screen_sharing_active:
                self.show_toast("⚠️ Screen sharing not active", "warning")
                return
            
            # Stop frame timer
            self.stop_basic_screen_sharing_timer()
            
            # Stop screen capture
            self.screen_capture.stop_capture()
            
            # Notify students
            await self.network_manager.broadcast_message("screen_sharing", {
                "action": "stop"
            })
            
            # Update UI
            self.screen_sharing_active = False
            self.start_sharing_btn.setEnabled(True)
            self.stop_sharing_btn.setEnabled(False)
            
            self.show_toast("🚫 Screen sharing stopped", "info")
            self.logger.info("Screen sharing stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping screen sharing: {e}")
            self.show_toast(f"❌ Error stopping screen sharing: {str(e)}", "error")
    
    def create_right_panel(self):
        """Create right student panel"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
    def refresh_student_list(self):
        """Refresh the student list display with real IP addresses and actions"""
        try:
            self.student_table.setRowCount(len(self.connected_students))
            
            for row, (client_id, student_info) in enumerate(self.connected_students.items()):
                # Name
                name_item = QTableWidgetItem(student_info.get("name", "Unknown"))
                self.student_table.setItem(row, 0, name_item)
                
                # Real IP Address
                ip_item = QTableWidgetItem(student_info.get("ip_address", "unknown"))
                self.student_table.setItem(row, 1, ip_item)
                
                # Status
                status = student_info.get("status", "connected")
                status_item = QTableWidgetItem(status.title())
                if status == "connected":
                    status_item.setStyleSheet("color: green; font-weight: bold;")
                else:
                    status_item.setStyleSheet("color: red; font-weight: bold;")
                self.student_table.setItem(row, 2, status_item)
                
                # Battery
                battery_level = student_info.get("battery_level", 100)
                is_charging = student_info.get("is_charging", True)
                battery_text = f"{battery_level}%"
                if is_charging:
                    battery_text += " 🔌"
                if battery_level < 20:
                    battery_text += " ⚠️"
                battery_item = QTableWidgetItem(battery_text)
                self.student_table.setItem(row, 3, battery_item)
                
                # Violations
                violations = student_info.get("violations", 0)
                violations_item = QTableWidgetItem(str(violations))
                if violations > 0:
                    violations_item.setStyleSheet("color: red; font-weight: bold;")
                self.student_table.setItem(row, 4, violations_item)
                
                # Keystrokes
                keystrokes = student_info.get("keystrokes", 0)
                keystrokes_item = QTableWidgetItem(str(keystrokes))
                self.student_table.setItem(row, 5, keystrokes_item)
                
                # Focus Mode
                focus_mode = student_info.get("focus_mode", False)
                focus_text = "ON" if focus_mode else "OFF"
                focus_item = QTableWidgetItem(focus_text)
                if focus_mode:
                    focus_item.setStyleSheet("color: red; font-weight: bold;")
                else:
                    focus_item.setStyleSheet("color: green;")
                self.student_table.setItem(row, 6, focus_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)
                
                # Kick button
                kick_btn = QPushButton("📴")
                kick_btn.setToolTip("Disconnect Student")
                kick_btn.setMaximumSize(30, 25)
                kick_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                kick_btn.clicked.connect(lambda checked, cid=client_id: self.kick_student(cid))
                actions_layout.addWidget(kick_btn)
                
                # Monitor button
                monitor_btn = QPushButton("👁️")
                monitor_btn.setToolTip("View Student Screen")
                monitor_btn.setMaximumSize(30, 25)
                monitor_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #007bff;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #0056b3;
                    }
                """)
                monitor_btn.clicked.connect(lambda checked, cid=client_id: self.monitor_student(cid))
                actions_layout.addWidget(monitor_btn)
                
                # Focus button
                focus_btn = QPushButton("🎯")
                focus_btn.setToolTip("Toggle Focus Mode")
                focus_btn.setMaximumSize(30, 25)
                focus_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffc107;
                        color: black;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #e0a800;
                    }
                """)
                focus_btn.clicked.connect(lambda checked, cid=client_id: self.toggle_student_focus(cid))
                actions_layout.addWidget(focus_btn)
                
                actions_layout.addStretch()
                self.student_table.setCellWidget(row, 7, actions_widget)
            
            # Update student count
            self.student_count_label.setText(f"({len(self.connected_students)})")
            
        except Exception as e:
            self.logger.error(f"Error refreshing student list: {e}")
    
    def kick_student(self, client_id: str):
        """Disconnect a student"""
        try:
            if client_id in self.connected_students:
                student_name = self.connected_students[client_id].get("name", "Unknown")
                
                # Send disconnect message
                self.schedule_async_task(self.network_manager._send_message(client_id, "force_disconnect", {
                    "reason": "Disconnected by teacher"
                }))
                
                self.show_toast(f"📴 Kicked {student_name}", "warning")
                self.logger.info(f"Kicked student: {student_name}")
                
        except Exception as e:
            self.logger.error(f"Error kicking student: {e}")
    
    def monitor_student(self, client_id: str):
        """Request student screen view"""
        try:
            if client_id in self.connected_students:
                student_name = self.connected_students[client_id].get("name", "Unknown")
                
                # Send screen request
                self.schedule_async_task(self.network_manager._send_message(client_id, "screen_request", {
                    "action": "request_screen"
                }))
                
                self.show_toast(f"👁️ Requesting screen from {student_name}", "info")
                self.logger.info(f"Requested screen from: {student_name}")
                
        except Exception as e:
            self.logger.error(f"Error requesting student screen: {e}")
    
    def toggle_student_focus(self, client_id: str):
        """Toggle focus mode for specific student"""
        try:
            if client_id in self.connected_students:
                student_name = self.connected_students[client_id].get("name", "Unknown")
                current_focus = self.connected_students[client_id].get("focus_mode", False)
                new_focus = not current_focus
                
                # Update local state
                self.connected_students[client_id]["focus_mode"] = new_focus
                
                # Send focus mode change
                self.schedule_async_task(self.network_manager._send_message(client_id, "focus_mode", {
                    "enabled": new_focus
                }))
                
                # Refresh display
                self.refresh_student_list()
                
                action = "enabled" if new_focus else "disabled"
                self.show_toast(f"🎯 Focus mode {action} for {student_name}", "info")
                self.logger.info(f"Focus mode {action} for: {student_name}")
                
        except Exception as e:
            self.logger.error(f"Error toggling student focus: {e}")
    
    def start_session(self):
        """Start a new session"""
        self.schedule_async_task(self._start_session_async())
    
    async def _start_session_async(self):
        """Async session start"""
        try:
            self.show_toast("🚀 Starting new session...", "info")
            
            # Generate session details
            from common.network_manager import generate_session_code, generate_session_password
            session_code = generate_session_code()
            password = generate_session_password()
            
            # Initialize database
            await self.db_manager.initialize_database()
            
            # Create session in database
            teacher_ip = get_local_ip()
            self.session_id = await self.db_manager.create_session(
                session_code, password, teacher_ip
            )
            
            # Start network server
            server_info = await self.network_manager.start_teacher_server(session_code, password)
            
            # Update UI with session details
            self.session_code_label.setText(session_code)
            self.password_label.setText(password)
            self.ip_label.setText(teacher_ip)
            
            # Generate QR code with enhanced data
            qr_data = {
                "type": "focusclass_session",
                "teacher_ip": teacher_ip,
                "session_code": session_code,
                "password": password,
                "version": "1.0.0",
                "websocket_port": 8765,
                "http_port": 8080
            }
            
            import json
            from common.utils import create_qr_code
            qr_image = create_qr_code(json.dumps(qr_data), size=200)
            
            # Convert PIL image to QPixmap
            from io import BytesIO
            buffer = BytesIO()
            qr_image.save(buffer, format="PNG")
            buffer.seek(0)
            qr_pixmap = QPixmap()
            qr_pixmap.loadFromData(buffer.getvalue())
            
            # Scale QR code to fit label
            scaled_pixmap = qr_pixmap.scaled(
                self.qr_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.qr_label.setPixmap(scaled_pixmap)
            
            # Update button states
            self.session_active = True
            self.start_session_btn.setEnabled(False)
            self.stop_session_btn.setEnabled(True)
            self.focus_mode_checkbox.setEnabled(True)
            self.start_sharing_btn.setEnabled(True)
            self.copy_session_btn.setEnabled(True)
            self.view_details_btn.setEnabled(True)
            
            # Start refresh timer
            self.refresh_timer.start(5000)  # 5 seconds
            
            # Update status
            self.status_label.setText(f"Session active: {session_code}")
            
            self.show_toast(f"✅ Session started! Code: {session_code}", "success")
            self.logger.info(f"Session started: {session_code}")
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            self.show_toast(f"❌ Failed to start session: {str(e)}", "error")
    
    def stop_session(self):
        """Stop the current session"""
        self.schedule_async_task(self._stop_session_async())
    
    async def _stop_session_async(self):
        """Async session stop"""
        try:
            self.show_toast("🛁 Stopping session...", "info")
            
            # End session in database
            if self.session_id:
                await self.db_manager.end_session(self.session_id)
            
            # Stop network server
            await self.network_manager.stop_server()
            
            # Stop screen sharing if active
            if self.screen_sharing_active:
                await self._stop_screen_sharing_async()
            
            # Reset UI
            self.session_code_label.setText("Not started")
            self.password_label.setText("Not started")
            self.qr_label.clear()
            self.qr_label.setText("QR Code will appear here")
            
            # Update button states
            self.session_active = False
            self.start_session_btn.setEnabled(True)
            self.stop_session_btn.setEnabled(False)
            self.focus_mode_checkbox.setEnabled(False)
            self.focus_mode_checkbox.setChecked(False)
            self.start_sharing_btn.setEnabled(False)
            self.stop_sharing_btn.setEnabled(False)
            self.copy_session_btn.setEnabled(False)
            self.view_details_btn.setEnabled(False)
            
            # Clear data
            self.connected_students.clear()
            self.refresh_student_list()
            
            # Stop timers
            self.refresh_timer.stop()
            
            # Update status
            self.status_label.setText("Ready")
            
            self.show_toast("✅ Session ended successfully", "success")
            self.logger.info("Session ended")
            
        except Exception as e:
            self.logger.error(f"Error stopping session: {e}")
            self.show_toast(f"❌ Error stopping session: {str(e)}", "error")
    
    def toggle_focus_mode(self, enabled: bool):
        """Toggle focus mode for all students"""
        self.schedule_async_task(self._toggle_focus_mode_async(enabled))
    
    async def _toggle_focus_mode_async(self, enabled: bool):
        """Async focus mode toggle"""
        try:
            if self.session_id:
                await self.db_manager.update_focus_mode(self.session_id, enabled)
            
            # Broadcast to all students
            await self.network_manager.broadcast_message("focus_mode", {
                "enabled": enabled
            })
            
            # Update all students' focus mode status
            for client_id in self.connected_students:
                self.connected_students[client_id]["focus_mode"] = enabled
            
            self.focus_mode_active = enabled
            self.refresh_student_list()
            
            action = "enabled" if enabled else "disabled"
            self.show_toast(f"🎯 Focus mode {action} for all students", "info")
            self.logger.info(f"Focus mode {action}")
            
        except Exception as e:
            self.logger.error(f"Error changing focus mode: {e}")
            self.show_toast(f"❌ Error changing focus mode: {str(e)}", "error")
    
    def clear_violation_log(self):
        """Clear the violation log"""
        self.violation_log.clear()
        self.show_toast("🗁️ Violation log cleared", "info")
    
    def clear_malicious_activities(self):
        """Clear malicious activities log"""
        self.malicious_list.clear()
        self.show_toast("🗁️ Malicious activities cleared", "info")
    
    def export_activity_report(self):
        """Export activity report"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import datetime
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Activity Report", 
                f"focusclass_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"FocusClass Activity Report\n")
                    f.write(f"Generated: {datetime.datetime.now()}\n\n")
                    
                    # Session info
                    if self.session_active:
                        f.write(f"Session Code: {self.session_code_label.text()}\n")
                        f.write(f"Teacher IP: {self.ip_label.text()}\n")
                    
                    # Connected students
                    f.write(f"\nConnected Students ({len(self.connected_students)}):\n")
                    for client_id, info in self.connected_students.items():
                        f.write(f"- {info.get('name', 'Unknown')} ({info.get('ip_address', 'unknown')})\n")
                        f.write(f"  Violations: {info.get('violations', 0)}\n")
                        f.write(f"  Keystrokes: {info.get('keystrokes', 0)}\n")
                        f.write(f"  Battery: {info.get('battery_level', 100)}%\n")
                    
                    # Violations
                    f.write(f"\nViolations:\n")
                    f.write(self.violation_log.toPlainText())
                    
                    # Malicious activities
                    f.write(f"\nMalicious Activities:\n")
                    f.write(self.malicious_list.toPlainText())
                
                self.show_toast(f"📄 Report exported to {filename}", "success")
                
        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
            self.show_toast(f"❌ Error exporting report: {str(e)}", "error")
    
    def setup_timers(self):
        """Setup periodic timers"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_student_list)
        
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance_stats)
        self.performance_timer.start(5000)
    
    def update_performance_stats(self):
        """Update performance statistics"""
        try:
            # Update network label with current info
            if hasattr(self, 'network_label'):
                local_ip = get_local_ip()
                self.network_label.setText(f"IP: {local_ip}")
            
        except Exception as e:
            self.logger.error(f"Error updating performance stats: {e}")
        
        # Student table with enhanced columns
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(8)
        self.student_table.setHorizontalHeaderLabels([
            "Name", "IP Address", "Status", "Battery", "Violations", "Keystrokes", "Focus", "Actions"
        ])
        self.student_table.horizontalHeader().setStretchLastSection(True)
        self.student_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        right_layout.addWidget(self.student_table)
        
        # Malicious activity panel
        malicious_group = QGroupBox("Malicious Activities")
        malicious_layout = QVBoxLayout(malicious_group)
        
        self.malicious_list = QTextEdit()
        self.malicious_list.setReadOnly(True)
        self.malicious_list.setMaximumHeight(120)
        self.malicious_list.setStyleSheet("""
            QTextEdit {
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        malicious_layout.addWidget(self.malicious_list)
        
        # Malicious activity controls
        malicious_controls = QHBoxLayout()
        self.clear_malicious_btn = QPushButton("Clear Activities")
        self.export_report_btn = QPushButton("Export Report")
        self.clear_malicious_btn.clicked.connect(self.clear_malicious_activities)
        self.export_report_btn.clicked.connect(self.export_activity_report)
        
        malicious_controls.addWidget(self.clear_malicious_btn)
        malicious_controls.addWidget(self.export_report_btn)
        malicious_controls.addStretch()
        malicious_layout.addLayout(malicious_controls)
        
        right_layout.addWidget(malicious_group)
        
        return right_panel
    
    def setup_timers(self):
        """Setup periodic timers"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_student_list)
        
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance_stats)
        self.performance_timer.start(5000)
    
    def setup_signals(self):
        """Setup signal connections"""
        self.setup_network_handlers()
    
    def setup_network_handlers(self):
        """Setup network event handlers"""
        self.network_manager.register_message_handler("authenticate", self.handle_student_authentication)
        self.network_manager.register_message_handler("violation", self.handle_violation)
        self.network_manager.register_message_handler("heartbeat", self.handle_heartbeat)
        self.network_manager.register_message_handler("keystroke_data", self.handle_keystroke_data)
        self.network_manager.register_message_handler("battery_status", self.handle_battery_status)
        self.network_manager.register_message_handler("system_info", self.handle_system_info)
        self.network_manager.register_message_handler("malicious_activity", self.handle_malicious_activity)
        
        self.network_manager.register_connection_handler("connection", self.handle_student_connection)
        self.network_manager.register_connection_handler("disconnection", self.handle_student_disconnection)
    
    def start_session(self):
        """Start a new session"""
        self.schedule_async_task(self._start_session_async())
    
    async def _start_session_async(self):
        """Async session start"""
        try:
            self.show_toast("🚀 Starting new session...", "info")
            
            # Generate session details
            session_code = generate_session_code()
            password = generate_session_password()
            
            # Initialize database
            await self.db_manager.initialize_database()
            
            # Create session in database
            teacher_ip = get_local_ip()
            self.session_id = await self.db_manager.create_session(
                session_code, password, teacher_ip
            )
            
            # Start network server
            await self.network_manager.start_teacher_server(session_code, password)
            
            # Update UI
            self.session_code_label.setText(session_code)
            self.password_label.setText(password)
            
            # Generate QR code
            qr_data = {
                "type": "focusclass_session",
                "teacher_ip": teacher_ip,
                "session_code": session_code,
                "password": password,
                "version": "1.0.0"
            }
            
            qr_image = create_qr_code(qr_data, size=200)  # Increased size
            
            # Convert PIL image to QPixmap using PNG bytes
            buffer = BytesIO()
            qr_image.save(buffer, format="PNG")
            buffer.seek(0)
            qr_pixmap = QPixmap()
            qr_pixmap.loadFromData(buffer.getvalue())
            
            # Scale QR code to fit label
            scaled_pixmap = qr_pixmap.scaled(
                self.qr_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.qr_label.setPixmap(scaled_pixmap)
            
            # Update button states
            self.session_active = True
            self.start_session_btn.setEnabled(False)
            self.stop_session_btn.setEnabled(True)
            self.focus_mode_checkbox.setEnabled(True)
            self.start_sharing_btn.setEnabled(True)
            self.copy_session_btn.setEnabled(True)  # Enable copy button
            self.view_details_btn.setEnabled(True)  # Enable view details button
            
            # Start refresh timer
            self.refresh_timer.start(5000)  # 5 seconds
            
            # Update status
            self.status_label.setText(f"Session active: {session_code}")
            
            self.show_toast(f"✅ Session started! Code: {session_code}", "success")
            self.logger.info(f"Session started: {session_code}")
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            self.show_toast(f"❌ Failed to start session: {str(e)}", "error")
    
    def stop_session(self):
        """Stop the current session"""
        reply = QMessageBox.question(
            self, "Stop Session",
            "Are you sure you want to stop the session?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.schedule_async_task(self._stop_session_async())
    
    async def _stop_session_async(self):
        """Async session stop"""
        try:
            self.show_toast("🛑 Stopping session...", "info")
            
            if self.session_id:
                await self.db_manager.end_session(self.session_id)
            
            await self.network_manager.stop_server()
            
            if self.screen_sharing_active:
                self.screen_capture.stop_capture()
                self.screen_sharing_active = False
            
            # Reset UI
            self.session_code_label.setText("Not started")
            self.password_label.setText("Not started")
            self.qr_label.clear()
            self.qr_label.setText("QR Code will appear here")
            
            # Update button states
            self.session_active = False
            self.start_session_btn.setEnabled(True)
            self.stop_session_btn.setEnabled(False)
            self.focus_mode_checkbox.setEnabled(False)
            self.focus_mode_checkbox.setChecked(False)
            self.start_sharing_btn.setEnabled(False)
            self.stop_sharing_btn.setEnabled(False)
            self.copy_session_btn.setEnabled(False)  # Disable copy button
            self.view_details_btn.setEnabled(False)  # Disable view details button
            
            # Clear data
            self.connected_students.clear()
            self.refresh_student_list()
            
            # Stop timers
            self.refresh_timer.stop()
            
            # Update status
            self.status_label.setText("Ready")
            
            self.show_toast("✅ Session ended successfully", "success")
            self.logger.info("Session ended")
            
        except Exception as e:
            self.logger.error(f"Error ending session: {e}")
    
    def toggle_focus_mode(self, enabled: bool):
        """Toggle focus mode"""
        self.schedule_async_task(self._toggle_focus_mode_async(enabled))
    
    async def _toggle_focus_mode_async(self, enabled: bool):
        """Async focus mode toggle"""
        try:
            if self.session_id:
                await self.db_manager.update_focus_mode(self.session_id, enabled)
            
            # Broadcast to all students
            await self.network_manager.broadcast_message("focus_mode", {
                "enabled": enabled
            })
            
            self.focus_mode_active = enabled
            self.logger.info(f"Focus mode {'enabled' if enabled else 'disabled'}")
            
        except Exception as e:
            self.logger.error(f"Error changing focus mode: {e}")
    
    def copy_session_details(self):
        """Copy session details to clipboard"""
        try:
            if self.session_active:
                session_code = self.session_code_label.text()
                password = self.password_label.text()
                teacher_ip = self.ip_label.text()
                
                session_details = f"""FocusClass Session Details:
                
📋 Session Code: {session_code}
🔑 Password: {password}
🌐 Teacher IP: {teacher_ip}

📱 Quick Join Link: focusclass://join?code={session_code}&password={password}&ip={teacher_ip}

🗓️ Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                # Copy to clipboard
                from PyQt5.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(session_details)
                
                self.show_toast("📋 Session details copied to clipboard!", "success")
                self.logger.info("Session details copied to clipboard")
            else:
                self.show_toast("⚠️ No active session to copy", "warning")
                
        except Exception as e:
            self.logger.error(f"Error copying session details: {e}")
            self.show_toast(f"❌ Failed to copy session details: {str(e)}", "error")
    
    def view_session_details(self):
        """Show session details in a dialog"""
        try:
            if not self.session_active:
                self.show_toast("⚠️ No active session to view", "warning")
                return
                
            session_code = self.session_code_label.text()
            password = self.password_label.text()
            teacher_ip = self.ip_label.text()
            
            # Create dialog
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QDialogButtonBox
            dialog = QDialog(self)
            dialog.setWindowTitle("📋 Session Details")
            dialog.setMinimumSize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Session info display
            info_text = QTextEdit()
            info_text.setReadOnly(True)
            info_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 14px;
                }
            """)
            
            session_info = f"""<div style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #2c3e50; margin-bottom: 20px;">🎯 FocusClass Session</h2>
            
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h3 style="color: #27ae60; margin-top: 0;">📋 Session Code</h3>
                <p style="font-size: 18px; font-weight: bold; color: #2c3e50; margin: 5px 0; font-family: 'Courier New', monospace;">{session_code}</p>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h3 style="color: #856404; margin-top: 0;">🔑 Password</h3>
                <p style="font-size: 16px; font-weight: bold; color: #2c3e50; margin: 5px 0; font-family: 'Courier New', monospace;">{password}</p>
            </div>
            
            <div style="background: #d1ecf1; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h3 style="color: #0c5460; margin-top: 0;">🌐 Teacher IP Address</h3>
                <p style="font-size: 16px; font-weight: bold; color: #2c3e50; margin: 5px 0; font-family: 'Courier New', monospace;">{teacher_ip}</p>
            </div>
            
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h3 style="color: #721c24; margin-top: 0;">📱 Quick Join Link</h3>
                <p style="font-size: 12px; color: #2c3e50; margin: 5px 0; word-break: break-all;">focusclass://join?code={session_code}&password={password}&ip={teacher_ip}</p>
            </div>
            
            <div style="background: #e2e3e5; padding: 15px; border-radius: 8px;">
                <h3 style="color: #383d41; margin-top: 0;">🗓️ Session Info</h3>
                <p style="margin: 5px 0;"><strong>Created:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p style="margin: 5px 0;"><strong>Connected Students:</strong> {len(self.connected_students)}</p>
                <p style="margin: 5px 0;"><strong>Status:</strong> Active 🟢</p>
            </div>
            </div>"""
            
            info_text.setHtml(session_info)
            layout.addWidget(info_text)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            copy_btn = QPushButton("📋 Copy Details")
            copy_btn.clicked.connect(lambda: self.copy_session_details())
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            
            close_btn = QPushButton("❌ Close")
            close_btn.clicked.connect(dialog.close)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            
            button_layout.addWidget(copy_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"Error viewing session details: {e}")
            self.show_toast(f"❌ Failed to view session details: {str(e)}", "error")
    
    def start_screen_sharing(self):
        """Start screen sharing"""
        try:
            self.show_toast("🚀 Starting screen sharing...", "info")
            
            self.screen_capture.set_quality("medium")
            capture_track = self.screen_capture.start_capture()
            
            if capture_track:
                self.screen_sharing_active = True
                self.start_sharing_btn.setEnabled(False)
                self.stop_sharing_btn.setEnabled(True)
                
                # Broadcast screen sharing start to all students
                self.schedule_async_task(self.network_manager.broadcast_message("screen_sharing", {
                    "enabled": True,
                    "quality": "medium",
                    "mode": "webrtc" if hasattr(capture_track, 'recv') else "basic"
                }))
                
                if hasattr(capture_track, 'recv'):
                    self.show_toast("✅ WebRTC screen sharing started!", "success")
                else:
                    self.show_toast("✅ Basic screen sharing started!", "warning")
                    # Start basic sharing timer for non-WebRTC mode
                    self.start_basic_screen_sharing_timer()
                    
                self.logger.info("Screen sharing started")
            else:
                self.show_toast("❌ Failed to start screen capture", "error")
                raise Exception("Failed to create screen capture track")
            
        except Exception as e:
            self.logger.error(f"Error starting screen sharing: {e}")
            self.show_toast(f"❌ Failed to start screen sharing: {str(e)}", "error")
    
    def stop_screen_sharing(self):
        """Stop screen sharing"""
        try:
            self.show_toast("🛑 Stopping screen sharing...", "info")
            
            # Stop basic sharing timer if active
            self.stop_basic_screen_sharing_timer()
            
            self.screen_capture.stop_capture()
            self.screen_sharing_active = False
            
            self.start_sharing_btn.setEnabled(True)
            self.stop_sharing_btn.setEnabled(False)
            
            # Broadcast screen sharing stop to all students
            self.schedule_async_task(self.network_manager.broadcast_message("screen_sharing", {
                "enabled": False
            }))
            
            self.show_toast("✅ Screen sharing stopped", "success")
            self.logger.info("Screen sharing stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping screen sharing: {e}")
            self.show_toast(f"❌ Failed to stop screen sharing: {str(e)}", "error")
    
    async def handle_student_authentication(self, client_id: str, data: Dict[str, Any]):
        """Handle student authentication"""
        try:
            student_name = data.get("student_name")
            password = data.get("password")
            session_code = data.get("session_code")
            
            # TODO: Verify session and password
            # For now, accept all connections
            
            # Get student IP
            student_ip = "127.0.0.1"  # Placeholder
            
            # Add student to database
            student_db_id = await self.db_manager.add_student(
                self.session_id, student_name, student_ip
            )
            
            # Store student info with enhanced data
            self.connected_students[client_id] = {
                "db_id": student_db_id,
                "name": student_name,
                "ip": student_ip,
                "status": "connected",
                "violations": 0,
                "keystroke_count": 0,
                "battery_level": 100,
                "is_charging": True,
                "focus_active": False,
                "join_time": time.time(),
                "last_seen": time.time(),
                "system_info": {},
                "recent_activities": ""
            }
            
            # Send success response with enhanced configuration
            await self.network_manager._send_message(client_id, "auth_success", {
                "student_id": client_id,
                "focus_mode": self.focus_mode_active,
                "keystroke_monitoring": self.keystroke_monitoring,
                "battery_monitoring": self.charging_monitoring,
                "restrictions": {
                    "no_tab_switching": True,
                    "no_window_minimize": True,
                    "no_external_apps": True
                }
            })
            
            self.logger.info(f"Student authenticated: {student_name}")
            
        except Exception as e:
            self.logger.error(f"Error handling authentication: {e}")
    
    async def handle_violation(self, client_id: str, data: Dict[str, Any]):
        """Handle violation report"""
        try:
            if client_id not in self.connected_students:
                return
            
            student = self.connected_students[client_id]
            student["violations"] += 1
            
            violation_type = data.get("type", "unknown")
            description = data.get("description", "")
            
            # Log in database
            await self.db_manager.log_violation(
                self.session_id, student["db_id"], violation_type, description
            )
            
            # Add to violation log
            timestamp = time.strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {student['name']}: {violation_type} - {description}"
            self.violation_log.append(log_entry)
            
            self.logger.warning(f"Violation from {student['name']}: {violation_type}")
            
        except Exception as e:
            self.logger.error(f"Error handling violation: {e}")
    
    async def handle_keystroke_data(self, client_id: str, data: Dict[str, Any]):
        """Handle keystroke monitoring data"""
        try:
            if client_id not in self.connected_students:
                return
            
            student = self.connected_students[client_id]
            keystroke_count = data.get("count", 0)
            student["keystroke_count"] = keystroke_count
            
            # Check for suspicious keystroke patterns
            if keystroke_count > 1000:  # High keystroke activity
                await self.log_malicious_activity(
                    client_id, "high_keystroke_activity", 
                    f"Excessive keystroke activity: {keystroke_count} keystrokes"
                )
            
            # Log to database
            await self.db_manager.log_activity(
                self.session_id, student["db_id"], "keystroke_data", 
                json.dumps({"count": keystroke_count})
            )
            
        except Exception as e:
            self.logger.error(f"Error handling keystroke data: {e}")
    
    async def handle_battery_status(self, client_id: str, data: Dict[str, Any]):
        """Handle battery status monitoring"""
        try:
            if client_id not in self.connected_students:
                return
            
            student = self.connected_students[client_id]
            battery_level = data.get("level", 100)
            is_charging = data.get("charging", False)
            
            student["battery_level"] = battery_level
            student["is_charging"] = is_charging
            
            # Check for low battery
            if battery_level < self.battery_threshold and not is_charging:
                await self.log_malicious_activity(
                    client_id, "low_battery", 
                    f"Low battery warning: {battery_level}% (not charging)"
                )
            
            # Log to database
            await self.db_manager.log_activity(
                self.session_id, student["db_id"], "battery_status", 
                json.dumps({"level": battery_level, "charging": is_charging})
            )
            
        except Exception as e:
            self.logger.error(f"Error handling battery status: {e}")
    
    async def handle_system_info(self, client_id: str, data: Dict[str, Any]):
        """Handle system information"""
        try:
            if client_id not in self.connected_students:
                return
            
            student = self.connected_students[client_id]
            student["system_info"] = data
            
            # Check for suspicious system changes
            cpu_usage = data.get("cpu_usage", 0)
            memory_usage = data.get("memory_usage", 0)
            
            if cpu_usage > 80:
                await self.log_malicious_activity(
                    client_id, "high_cpu_usage", 
                    f"High CPU usage detected: {cpu_usage}%"
                )
            
            if memory_usage > 85:
                await self.log_malicious_activity(
                    client_id, "high_memory_usage", 
                    f"High memory usage detected: {memory_usage}%"
                )
            
        except Exception as e:
            self.logger.error(f"Error handling system info: {e}")
    
    async def handle_malicious_activity(self, client_id: str, data: Dict[str, Any]):
        """Handle reported malicious activity"""
        try:
            activity_type = data.get("type", "unknown")
            description = data.get("description", "")
            severity = data.get("severity", "medium")
            
            await self.log_malicious_activity(client_id, activity_type, description, severity)
            
        except Exception as e:
            self.logger.error(f"Error handling malicious activity: {e}")
    
    async def log_malicious_activity(self, client_id: str, activity_type: str, description: str, severity: str = "medium"):
        """Log malicious activity"""
        try:
            if client_id not in self.connected_students:
                return
            
            student = self.connected_students[client_id]
            timestamp = time.time()
            
            # Store in local malicious activities
            if client_id not in self.malicious_activities:
                self.malicious_activities[client_id] = []
            
            activity = {
                "type": activity_type,
                "description": description,
                "severity": severity,
                "timestamp": timestamp
            }
            
            self.malicious_activities[client_id].append(activity)
            
            # Add to UI
            timestamp_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            severity_color = {
                "low": "#28a745",
                "medium": "#ffc107", 
                "high": "#dc3545"
            }.get(severity, "#6c757d")
            
            log_entry = f"""<span style="color: {severity_color}; font-weight: bold;">[{timestamp_str}] {student.get('name', 'Unknown')}</span><br>
            <b>Type:</b> {activity_type}<br>
            <b>Severity:</b> {severity.upper()}<br>
            <b>Details:</b> {description}<br><hr>"""
            
            self.malicious_list.append(log_entry)
            
            # Log to database
            await self.db_manager.log_violation(
                self.session_id, student["db_id"], activity_type, description
            )
            
            self.logger.warning(f"Malicious activity from {student.get('name')}: {activity_type} - {description}")
            
        except Exception as e:
            self.logger.error(f"Error logging malicious activity: {e}")
    
    async def handle_heartbeat(self, client_id: str, data: Dict[str, Any]):
        """Handle heartbeat from student"""
        if client_id in self.connected_students:
            student = self.connected_students[client_id]
            student["last_seen"] = time.time()
            
            # Update focus status if provided
            if "focus_active" in data:
                student["focus_active"] = data["focus_active"]
            
            # Update system stats if provided
            if "system_stats" in data:
                system_stats = data["system_stats"]
                student.update(system_stats)
    
    async def handle_student_connection(self, client_id: str, websocket):
        """Handle new student connection"""
        self.logger.info(f"New student connection: {client_id}")
    
    async def handle_student_disconnection(self, client_id: str):
        """Handle student disconnection"""
        if client_id in self.connected_students:
            student = self.connected_students[client_id]
            
            # Update database
            await self.db_manager.remove_student(student["db_id"])
            
            # Remove from local storage
            del self.connected_students[client_id]
            
            self.logger.info(f"Student disconnected: {student['name']}")
    
    def refresh_student_list(self):
        """Refresh the student table with enhanced information"""
        self.student_table.setRowCount(len(self.connected_students))
        
        for row, (client_id, student) in enumerate(self.connected_students.items()):
            # Name
            name_item = QTableWidgetItem(student.get("name", "Unknown"))
            self.student_table.setItem(row, 0, name_item)
            
            # IP
            ip_item = QTableWidgetItem(student.get("ip", "Unknown"))
            self.student_table.setItem(row, 1, ip_item)
            
            # Status
            status = student.get("status", "unknown")
            status_item = QTableWidgetItem(status.title())
            if status == "connected":
                status_item.setBackground(QColor(144, 238, 144))  # Light green
            elif status == "restricted":
                status_item.setBackground(QColor(255, 255, 0))  # Yellow
            self.student_table.setItem(row, 2, status_item)
            
            # Battery status
            battery_level = student.get("battery_level", 0)
            battery_item = QTableWidgetItem(f"{battery_level}%")
            if battery_level < self.battery_threshold:
                battery_item.setBackground(QColor(255, 99, 71))  # Red
            elif battery_level < 50:
                battery_item.setBackground(QColor(255, 255, 0))  # Yellow
            else:
                battery_item.setBackground(QColor(144, 238, 144))  # Green
            self.student_table.setItem(row, 3, battery_item)
            
            # Violations
            violations = student.get("violations", 0)
            violation_item = QTableWidgetItem(str(violations))
            if violations > 3:
                violation_item.setBackground(QColor(255, 99, 71))  # Red
            elif violations > 0:
                violation_item.setBackground(QColor(255, 255, 0))  # Yellow
            self.student_table.setItem(row, 4, violation_item)
            
            # Keystroke count
            keystrokes = student.get("keystroke_count", 0)
            keystroke_item = QTableWidgetItem(str(keystrokes))
            self.student_table.setItem(row, 5, keystroke_item)
            
            # Focus mode status
            focus_active = student.get("focus_active", False)
            focus_item = QTableWidgetItem("Active" if focus_active else "Inactive")
            if focus_active:
                focus_item.setBackground(QColor(144, 238, 144))  # Green
            else:
                focus_item.setBackground(QColor(255, 215, 0))  # Gold
            self.student_table.setItem(row, 6, focus_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            view_btn = QPushButton("View")
            view_btn.setMaximumWidth(50)
            view_btn.clicked.connect(lambda checked, cid=client_id: self.view_student_details(cid))
            
            kick_btn = QPushButton("Remove")
            kick_btn.setMaximumWidth(60)
            kick_btn.setStyleSheet("background-color: #f44336; color: white;")
            kick_btn.clicked.connect(lambda checked, cid=client_id: self.remove_student(cid))
            
            restrict_btn = QPushButton("Restrict")
            restrict_btn.setMaximumWidth(60)
            restrict_btn.clicked.connect(lambda checked, cid=client_id: self.toggle_student_restriction(cid))
            
            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(restrict_btn)
            actions_layout.addWidget(kick_btn)
            
            self.student_table.setCellWidget(row, 7, actions_widget)
        
        # Update count
        self.student_count_label.setText(f"({len(self.connected_students)})")
        self.students_label.setText(f"Students: {len(self.connected_students)}")
    
    def clear_violation_log(self):
        """Clear the violation log"""
        self.violation_log.clear()
    
    def clear_malicious_activities(self):
        """Clear malicious activities log"""
        self.malicious_list.clear()
        self.malicious_activities.clear()
    
    def export_activity_report(self):
        """Export activity report"""
        self.schedule_async_task(self._export_activity_report_async())
    
    async def _export_activity_report_async(self):
        """Async export activity report"""
        try:
            if self.session_id:
                # Export session data
                await self.db_manager.export_session_data(
                    self.session_id, "session_report.csv"
                )
                QMessageBox.information(self, "Success", "Report exported to session_report.csv")
            else:
                QMessageBox.warning(self, "Warning", "No active session to export")
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
    
    def view_student_details(self, client_id: str):
        """View detailed student information"""
        if client_id in self.connected_students:
            student = self.connected_students[client_id]
            details = f"""Student Details:
            
Name: {student.get('name', 'Unknown')}
IP Address: {student.get('ip', 'Unknown')}
Status: {student.get('status', 'Unknown')}
Battery Level: {student.get('battery_level', 0)}%
Violations: {student.get('violations', 0)}
Keystrokes: {student.get('keystroke_count', 0)}
Join Time: {time.ctime(student.get('join_time', 0))}
Focus Active: {student.get('focus_active', False)}

Recent Activities:
{student.get('recent_activities', 'No recent activities')}"""
            
            QMessageBox.information(self, f"Student: {student.get('name', 'Unknown')}", details)
    
    def remove_student(self, client_id: str):
        """Remove/kick a student from the session"""
        if client_id in self.connected_students:
            student = self.connected_students[client_id]
            reply = QMessageBox.question(
                self, "Remove Student",
                f"Are you sure you want to remove {student.get('name', 'Unknown')} from the session?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                asyncio.create_task(self._remove_student_async(client_id))
    
    async def _remove_student_async(self, client_id: str):
        """Async remove student"""
        try:
            # Send disconnect message to student
            await self.network_manager._send_message(client_id, "force_disconnect", {
                "reason": "Removed by teacher"
            })
            
            # Handle disconnection
            await self.handle_student_disconnection(client_id)
            
        except Exception as e:
            self.logger.error(f"Error removing student: {e}")
    
    def toggle_student_restriction(self, client_id: str):
        """Toggle student restriction level"""
        asyncio.create_task(self._toggle_student_restriction_async(client_id))
    
    async def _toggle_student_restriction_async(self, client_id: str):
        """Async toggle student restriction"""
        try:
            if client_id in self.connected_students:
                student = self.connected_students[client_id]
                current_status = student.get("status", "connected")
                
                if current_status == "connected":
                    new_status = "restricted"
                    restriction_level = "high"
                else:
                    new_status = "connected"
                    restriction_level = "normal"
                
                # Update local status
                student["status"] = new_status
                
                # Send restriction change to student
                await self.network_manager._send_message(client_id, "restriction_change", {
                    "level": restriction_level,
                    "status": new_status
                })
                
                self.logger.info(f"Changed restriction for {student.get('name')}: {restriction_level}")
                
        except Exception as e:
            self.logger.error(f"Error changing restriction: {e}")
    
    def update_performance_stats(self):
        """Update performance statistics"""
        # TODO: Implement performance monitoring
        pass
    
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
        
        event.accept()


async def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Setup async event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create main window
    window = TeacherMainWindow()
    window.show()
    
    # Run the application
    with loop:
        await loop.run_forever()


if __name__ == "__main__":
    if sys.platform == "win32":
        # Windows specific setup
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("FocusClass Teacher")
    
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)