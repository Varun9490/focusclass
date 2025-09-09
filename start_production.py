#!/usr/bin/env python3
"""
Production startup script for FocusClass
Handles proper error logging and graceful failures
"""

import sys
import os
import logging
from pathlib import Path
import traceback

def setup_logging():
    """Setup production logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "focusclass_startup.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("FocusClassStartup")

def check_dependencies():
    """Check if all required dependencies are available"""
    logger = logging.getLogger("FocusClassStartup")
    
    # Critical modules that are absolutely required
    critical_modules = [
        "PyQt5",
        "asyncio", 
        "websockets",
        "aiohttp",
        "aiosqlite",
        "PIL",
        "psutil",
        "mss",
        "qrcode"
    ]
    
    # Optional modules that enhance functionality but aren't critical
    optional_modules = [
        "pywin32",  # Windows-specific features
        "cv2",      # Advanced image processing
        "aiortc",   # WebRTC features
        "zeroconf"  # Network discovery
    ]
    
    missing_critical = []
    missing_optional = []
    
    # Check critical modules
    for module in critical_modules:
        try:
            __import__(module)
            logger.debug(f"OK {module} available")
        except ImportError:
            missing_critical.append(module)
            logger.warning(f"MISSING {module} (critical)")
    
    # Check optional modules
    for module in optional_modules:
        try:
            __import__(module)
            logger.debug(f"OK {module} available")
        except ImportError:
            missing_optional.append(module)
            logger.info(f"MISSING {module} (optional - some features may be disabled)")
    
    if missing_critical:
        logger.error(f"Missing critical modules: {', '.join(missing_critical)}")
        logger.error("Please install with: pip install -r requirements.txt")
        return False
    
    if missing_optional:
        logger.info(f"Optional modules not available: {', '.join(missing_optional)}")
        logger.info("Application will run with reduced functionality")
    
    logger.info("All critical dependencies are available")
    return True

def start_application():
    """Start the FocusClass application"""
    logger = logging.getLogger("FocusClassStartup")
    
    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        
        logger.info("Starting FocusClass Professional Edition...")
        
        # Import and start the main application
        from PyQt5.QtWidgets import QApplication
        import qasync
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("FocusClass Professional")
        app.setApplicationVersion("1.0.0")
        
        # Setup async event loop for Qt
        loop = qasync.QEventLoop(app)
        
        # Import main launcher
        try:
            from FocusClass import WelcomeWindow
            logger.info("Imported WelcomeWindow successfully")
        except ImportError as e:
            logger.error(f"Failed to import WelcomeWindow: {e}")
            # Fallback to direct teacher app
            from teacher.advanced_teacher_app import AdvancedTeacherApp
            window = AdvancedTeacherApp()
            window.show()
            logger.info("Started teacher app directly as fallback")
            
            with loop:
                loop.run_forever()
            return
        
        # Create main window
        main_window = WelcomeWindow()
        main_window.show()
        
        logger.info("FocusClass started successfully")
        
        # Run the application
        with loop:
            loop.run_forever()
            
    except Exception as e:
        logger.error(f"Critical error starting application: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    return True

def main():
    """Main entry point"""
    # Setup logging first
    logger = setup_logging()
    
    try:
        logger.info("="*50)
        logger.info("FocusClass Professional Edition - Starting Up")
        logger.info("="*50)
        
        # Check dependencies
        if not check_dependencies():
            logger.error("Dependency check failed. Cannot start application.")
            input("Press Enter to exit...")
            return 1
        
        # Start application
        if start_application():
            logger.info("Application exited normally")
            return 0
        else:
            logger.error("Application failed to start")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)