#!/usr/bin/env python3
"""
FocusClass Teacher Application Launcher
Production-ready launcher with full functionality
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Setup logging for the application"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "teacher_app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("FocusClassTeacher")

async def main():
    """Main application entry point"""
    logger = setup_logging()
    
    try:
        from PyQt5.QtWidgets import QApplication
        import qasync
        from teacher.advanced_teacher_app import AdvancedTeacherApp
        
        logger.info("Starting FocusClass Teacher Application...")
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("FocusClass Teacher")
        app.setApplicationVersion("1.0.0")
        
        # Setup async event loop
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Create and show teacher window
        teacher_window = AdvancedTeacherApp()
        teacher_window.show()
        
        logger.info("Teacher application started successfully!")
        logger.info("Teacher dashboard is ready for use.")
        logger.info("- Click 'Start Session' to begin a new teaching session")
        logger.info("- Session details will be displayed in the left panel")
        logger.info("- Students can connect using the session code and password")
        
        # Run the application
        with loop:
            await loop.run_forever()
            
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)