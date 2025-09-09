"""
FocusClass - Professional Classroom Management System
Main launcher with Teacher/Student mode selection
Requires Administrator privileges
"""

import sys
import os
import ctypes
import subprocess
import asyncio
from pathlib import Path

# Suppress Qt warnings
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts.warning=false'
os.environ['QT_QPA_PLATFORM'] = 'windows'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QFrame, QGridLayout, QGraphicsDropShadowEffect,
    QSplashScreen, QProgressBar, QDesktopWidget
)
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QLinearGradient, QBrush

from common.config import APP_NAME, APP_VERSION
from common.utils import setup_logging

# Import for error handling
try:
    from common.utils import setup_logging
except ImportError:
    def setup_logging(level, path):
        import logging
        logging.basicConfig(level=getattr(logging, level, logging.INFO))
        return logging.getLogger(__name__)


def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Request administrator privileges and restart"""
    if not is_admin():
        # Re-run the program with admin rights
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{__file__}"', None, 1
            )
            return False
        except:
            QMessageBox.critical(None, "Admin Required", 
                                 "Administrator privileges are required to run FocusClass.\n"
                                 "Please run as administrator.")
            return False
    return True


class ModernButton(QPushButton):
    """Modern styled button with animations and effects"""
    
    def __init__(self, text, color_scheme="blue", icon_text=""):
        super().__init__()
        self.setMinimumSize(280, 70)
        self.setMaximumSize(320, 80)
        self.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.setCursor(Qt.PointingHandCursor)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Set text with icon
        if icon_text:
            self.setText(f"{icon_text}  {text}")
        else:
            self.setText(text)
        
        # Color schemes
        color_schemes = {
            "blue": {
                "primary": "#4A90E2",
                "hover": "#357ABD",
                "pressed": "#2C5F8F",
                "gradient_start": "#5BA0F2",
                "gradient_end": "#4A90E2"
            },
            "green": {
                "primary": "#5CB85C",
                "hover": "#449D44",
                "pressed": "#357935",
                "gradient_start": "#6BC56B",
                "gradient_end": "#5CB85C"
            },
            "purple": {
                "primary": "#9B59B6",
                "hover": "#8E44AD",
                "pressed": "#7D3C98",
                "gradient_start": "#AF7AC5",
                "gradient_end": "#9B59B6"
            }
        }
        
        scheme = color_schemes.get(color_scheme, color_schemes["blue"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {scheme['gradient_start']}, stop:1 {scheme['gradient_end']});
                color: white;
                border: none;
                border-radius: 12px;
                padding: 20px 25px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {scheme['hover']}, stop:1 {scheme['primary']});
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background: {scheme['pressed']};
                transform: scale(0.98);
            }}
        """)
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def enterEvent(self, event):
        """Hover enter animation"""
        self.animate_scale(1.02)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hover leave animation"""
        self.animate_scale(1.0)
        super().leaveEvent(event)
    
    def animate_scale(self, scale):
        """Animate button scaling"""
        rect = self.geometry()
        center = rect.center()
        new_width = int(rect.width() * scale)
        new_height = int(rect.height() * scale)
        new_rect = QRect(0, 0, new_width, new_height)
        new_rect.moveCenter(center)
        
        self.animation.setStartValue(rect)
        self.animation.setEndValue(new_rect)
        self.animation.start()


class WelcomeWindow(QMainWindow):
    """Enhanced welcome window with modern material design"""
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logging("INFO", "logs/launcher.log")
        self.setup_ui()
        self.setup_animations()
        
    def setup_animations(self):
        """Setup entrance animations"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Start fade in animation
        QTimer.singleShot(100, self.fade_animation.start)
        
    def setup_ui(self):
        """Setup the enhanced modern UI with material design"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - Professional Edition")
        self.setFixedSize(800, 700)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        # Center the window
        self.center_window()
        
        # Modern material design styling
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
            }
            QLabel {
                color: #2c3e50;
            }
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                border: none;
            }
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.98), stop:1 rgba(255, 255, 255, 0.92));
                border-radius: 25px;
                border: 3px solid rgba(74, 144, 226, 0.3);
            }
            QFrame#featureFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(248, 249, 250, 0.95));
                border-radius: 20px;
                border: 2px solid rgba(74, 144, 226, 0.2);
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with better spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 30, 40, 30)
        
        # Header section with enhanced design
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(40, 30, 40, 30)
        header_layout.setSpacing(20)
        
        # Animated title with enhanced styling
        title_label = QLabel(f"🎓 {APP_NAME}")
        title_label.setFont(QFont("Segoe UI", 36, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4A90E2, stop:0.5 #9B59B6, stop:1 #4A90E2);
            margin-bottom: 10px;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        """)
        header_layout.addWidget(title_label)
        
        # Enhanced subtitle with animation
        subtitle_label = QLabel("Professional Classroom Management System")
        subtitle_label.setFont(QFont("Segoe UI Light", 16, QFont.Normal))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            color: #5a6c7d; 
            margin-bottom: 15px;
            font-weight: 300;
        """)
        header_layout.addWidget(subtitle_label)
        
        # Enhanced features highlight with icons
        features_frame = QFrame()
        features_frame.setObjectName("featureFrame")
        features_layout = QVBoxLayout(features_frame)
        features_layout.setContentsMargins(20, 15, 20, 15)
        
        features_title = QLabel("🚀 Key Features")
        features_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        features_title.setAlignment(Qt.AlignCenter)
        features_title.setStyleSheet("color: #4A90E2; margin-bottom: 8px;")
        features_layout.addWidget(features_title)
        
        features_grid = QGridLayout()
        features_grid.setSpacing(15)
        
        feature_items = [
            ("📊", "Real-time Analytics"),
            ("🔒", "Focus Control"),
            ("👥", "Student Monitoring"),
            ("📱", "QR Code Connection"),
            ("🖥️", "Screen Sharing"),
            ("⚡", "Lightning Fast")
        ]
        
        for i, (icon, text) in enumerate(feature_items):
            feature_widget = QWidget()
            feature_layout = QHBoxLayout(feature_widget)
            feature_layout.setContentsMargins(10, 5, 10, 5)
            
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI Emoji", 14))
            feature_layout.addWidget(icon_label)
            
            text_label = QLabel(text)
            text_label.setFont(QFont("Segoe UI", 11, QFont.Medium))
            text_label.setStyleSheet("color: #5a6c7d;")
            feature_layout.addWidget(text_label)
            
            features_grid.addWidget(feature_widget, i // 2, i % 2)
        
        features_layout.addLayout(features_grid)
        header_layout.addWidget(features_frame)
        
        # Enhanced version and admin status
        status_text = f"Version {APP_VERSION} • Build 2025.01"
        if is_admin():
            status_text += " • 🛡️ Administrator Mode Active"
            status_color = "#27ae60"
            status_bg = "rgba(39, 174, 96, 0.1)"
        else:
            status_text += " • ⚠️ Limited Mode (Administrator recommended)"
            status_color = "#e67e22"
            status_bg = "rgba(230, 126, 34, 0.1)"
            
        status_label = QLabel(status_text)
        status_label.setFont(QFont("Segoe UI", 11, QFont.Medium))
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet(f"""
            color: {status_color}; 
            background-color: {status_bg};
            padding: 12px 20px; 
            border-radius: 15px;
            border: 2px solid {status_color};
            margin-top: 10px;
        """)
        header_layout.addWidget(status_label)
        
        main_layout.addWidget(header_frame)
        
        # Mode selection section with enhanced design
        selection_frame = QFrame()
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.setContentsMargins(40, 30, 40, 30)
        selection_layout.setSpacing(25)
        
        mode_label = QLabel("Choose Your Experience")
        mode_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        mode_label.setAlignment(Qt.AlignCenter)
        mode_label.setStyleSheet("""
            color: #2c3e50;
            margin-bottom: 20px;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        """)
        selection_layout.addWidget(mode_label)
        
        # Enhanced buttons layout with descriptions
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(20)
        
        # Teacher mode container
        teacher_container = self.create_mode_container(
            "👨‍🏫", "Teacher Mode", 
            "Complete classroom control with advanced monitoring and analytics",
            "blue", self.launch_teacher
        )
        buttons_layout.addWidget(teacher_container)
        
        # Student mode container
        student_container = self.create_mode_container(
            "👨‍🎓", "Student Mode",
            "Connect to sessions with secure focus management and screen sharing",
            "green", self.launch_student
        )
        buttons_layout.addWidget(student_container)
        
        selection_layout.addLayout(buttons_layout)
        main_layout.addWidget(selection_frame)
        
        # Enhanced footer with additional features
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(20)
        
        # Quick access buttons with modern styling
        settings_btn = self.create_footer_button("⚙️", "Settings", "#6c757d", self.show_settings)
        help_btn = self.create_footer_button("❓", "Help", "#17a2b8", self.show_help)
        about_btn = self.create_footer_button("ℹ️", "About", "#9B59B6", self.show_about)
        
        footer_layout.addWidget(settings_btn)
        footer_layout.addStretch()
        
        footer_label = QLabel("© 2025 FocusClass Team. Crafted with 💙 for Education.")
        footer_label.setFont(QFont("Segoe UI", 10, QFont.Normal))
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: rgba(44, 62, 80, 0.7);")
        footer_layout.addWidget(footer_label)
        
        footer_layout.addStretch()
        footer_layout.addWidget(help_btn)
        footer_layout.addWidget(about_btn)
        
        main_layout.addLayout(footer_layout)
    
    # --- Start of Fix ---
    def create_mode_container(self, icon, title, description, color, callback):
        """Creates a styled container for a mode selection"""
        container = QFrame()
        container.setObjectName("featureFrame")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(20)

        # Text part
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        title_label = QLabel(f"{icon} {title}")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; background: transparent;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet("color: #5a6c7d; background: transparent;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout, 3) 

        # Button part
        button = ModernButton(f"Launch {title.split(' ')[0]}", color_scheme=color)
        button.clicked.connect(callback)
        button.setMinimumSize(200, 60)
        button.setMaximumSize(220, 70)
        
        layout.addWidget(button, 1, Qt.AlignCenter)
        
        return container
        
    def create_footer_button(self, icon, text, color, callback):
        """Creates a styled button for the footer"""
        button = QPushButton(f"{icon} {text}")
        button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                color: {color};
                background-color: transparent;
                border: none;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 8px;
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
        """)
        button.clicked.connect(callback)
        return button

    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        <h2>🎓 {APP_NAME} v{APP_VERSION}</h2>
        <p><b>Professional Classroom Management System</b></p>
        <p>© 2025 FocusClass Team. All rights reserved.</p>
        <p>This application is designed to enhance the learning environment
        by providing teachers with robust tools for classroom management and
        student engagement.</p>
        <p>For more information, visit our website:
        <a href='https://focusclass.app'>focusclass.app</a></p>
        """
        QMessageBox.about(self, f"About {APP_NAME}", about_text)
    # --- End of Fix ---
        
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "Settings", 
                                "Settings panel coming soon!\n\n"
                                "Current configuration can be found in:\n"
                                "src/common/config.py")
    
    def show_help(self):
        """Show help dialog"""
        help_text = f"""
        <h2>🎓 FocusClass Help</h2>
        
        <h3>👨‍🏫 Teacher Mode:</h3>
        <ul>
            <li>Create and manage classroom sessions</li>
            <li>Monitor student activities in real-time</li>
            <li>Control student focus modes and restrictions</li>
            <li>View comprehensive analytics and reports</li>
            <li>Share your screen with students</li>
        </ul>
        
        <h3>👨‍🎓 Student Mode:</h3>
        <ul>
            <li>Connect to teacher sessions via QR code or manual entry</li>
            <li>View teacher's shared screen</li>
            <li>Participate in focus mode when required</li>
            <li>Secure and monitored learning environment</li>
        </ul>
        
        <h3>⚙️ System Requirements:</h3>
        <ul>
            <li>Windows 10/11 (Administrator privileges recommended)</li>
            <li>Python 3.8+ with PyQt5</li>
            <li>Network connectivity for teacher-student communication</li>
        </ul>
        
        <p><b>For technical support, please check the README.md file.</b></p>
        """
        
        QMessageBox.about(self, "FocusClass Help", help_text)
        
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def launch_teacher(self):
        """Launch teacher application"""
        if not is_admin():
            QMessageBox.warning(self, "Admin Required", 
                                "Teacher mode requires administrator privileges for full functionality.")
            return
            
        try:
            # Try to use the advanced teacher app first
            from teacher.advanced_teacher_app import AdvancedTeacherApp
            self.hide()
            self.teacher_app = AdvancedTeacherApp()
            self.teacher_app.show()
            self.teacher_app.window_closed.connect(self.show_welcome)
            
        except ImportError as e:
            self.logger.error(f"Failed to load advanced teacher app: {e}")
            try:
                # Fallback to basic teacher app
                from teacher.teacher_app import TeacherMainWindow
                self.hide()
                self.teacher_app = TeacherMainWindow()
                self.teacher_app.show()
                # Basic app might not have window_closed signal
                if hasattr(self.teacher_app, 'window_closed'):
                    self.teacher_app.window_closed.connect(self.show_welcome)
                
            except ImportError as e2:
                QMessageBox.critical(self, "Error", 
                                     f"Failed to launch teacher application:\n{str(e2)}\n\n"
                                     "Please ensure all dependencies are installed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
            
    def launch_student(self):
        """Launch student application"""
        try:
            # Use the enhanced advanced student app
            from student.advanced_student_app import AdvancedStudentApp
            self.hide()
            self.student_app = AdvancedStudentApp()
            self.student_app.show()
            self.student_app.window_closed.connect(self.show_welcome)
            
        except ImportError as e:
            self.logger.error(f"Failed to load advanced student app: {e}")
            try:
                # Fallback to basic student app
                from student.student_app import StudentMainWindow
                self.hide()
                self.student_app = StudentMainWindow()
                self.student_app.show()
                # Basic app might not have window_closed signal
                if hasattr(self.student_app, 'window_closed'):
                    self.student_app.window_closed.connect(self.show_welcome)
                
            except ImportError as e2:
                QMessageBox.critical(self, "Error", 
                                     f"Failed to launch student application:\n{str(e2)}\n\n"
                                     "Please ensure all dependencies are installed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
            
    def show_welcome(self):
        """Show welcome window again"""
        self.show()
        
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(self, "Exit FocusClass",
                                     "Are you sure you want to exit FocusClass?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def create_splash_screen(app):
    """Create and show modern splash screen"""
    try:
        # Create splash screen
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(QColor(248, 249, 250))
        
        # Paint on splash screen
        painter = QPainter(splash_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background gradient
        from PyQt5.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, 300)
        gradient.setColorAt(0, QColor(0, 122, 204))
        gradient.setColorAt(1, QColor(0, 90, 158))
        painter.fillRect(splash_pixmap.rect(), gradient)
        
        # Title text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(splash_pixmap.rect(), Qt.AlignCenter, f"🎓 {APP_NAME}")
        
        # Version text
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(20, 270, f"Version {APP_VERSION} - Professional Edition")
        
        # Loading text
        painter.drawText(20, 250, "Loading...")
        
        painter.end()
        
        splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pixmap.mask())
        
        # Show splash
        splash.show()
        app.processEvents()
        
        return splash
        
    except Exception as e:
        print(f"Failed to create splash screen: {e}")
        return None


def main():
    """Enhanced main entry point with modern initialization"""
    import qasync
    
    # Check admin privileges first
    if not run_as_admin():
        return
    
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("FocusClass Team")
    app.setOrganizationDomain("focusclass.app")
    
    # Setup logging
    logger = setup_logging("INFO", "logs/launcher.log")
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    # Create and show splash screen
    splash = create_splash_screen(app)
    
    if splash:
        splash.showMessage("Initializing application...", Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
        app.processEvents()
        
        # Simulate loading time
        QTimer.singleShot(1500, lambda: splash.showMessage("Loading modules...", Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255)))
        QTimer.singleShot(2000, lambda: splash.showMessage("Starting interface...", Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255)))
    
    # Set application icon (if available)
    try:
        icon_path = Path("assets/icon.ico")
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        else:
            # Use default icon
            app.setWindowIcon(app.style().standardIcon(app.style().SP_ComputerIcon))
    except Exception as e:
        logger.warning(f"Could not set application icon: {e}")
    
    # Create welcome window after splash
    def show_welcome():
        if splash:
            splash.close()
        
        welcome = WelcomeWindow()
        welcome.show()
        
        # Check admin privileges and show warning if needed
        if not is_admin():
            QTimer.singleShot(1000, lambda: QMessageBox.warning(
                welcome, "Administrator Privileges Required",
                "FocusClass requires administrator privileges for full functionality.\n"
                "Some features may not work properly without admin rights.\n\n"
                "Please restart the application as administrator for the best experience."
            ))
        
        logger.info("Welcome window displayed")
        return welcome
    
    # Show welcome window after splash delay
    QTimer.singleShot(2500, show_welcome)
    
    # Use qasync event loop for proper asyncio integration
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    try:
        with loop:
            loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Application terminated by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Application error: {e}")
        QMessageBox.critical(None, "Application Error", 
                             f"An unexpected error occurred:\n{str(e)}\n\n"
                             "Please check the logs for more details.")
    finally:
        logger.info("Application shutdown")


if __name__ == "__main__":
    main()