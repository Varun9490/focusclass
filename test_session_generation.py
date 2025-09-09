#!/usr/bin/env python3
"""
Test script for session generation and UI functionality
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication
import qasync
from teacher.teacher_app import TeacherMainWindow

async def test_session_creation():
    """Test session creation functionality"""
    print("Testing session creation...")
    
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    try:
        window = TeacherMainWindow()
        window.show()
        
        print("Window created successfully")
        print("Testing session start...")
        
        # Test the session start functionality
        await window._start_session_async()
        
        print("Session started successfully!")
        print(f"Session Code: {window.session_code_label.text()}")
        print(f"Password: {window.password_label.text()}")
        print(f"Teacher IP: {window.ip_label.text()}")
        
        # Test clipboard functionality
        window.copy_session_details()
        print("Clipboard copy tested")
        
        # Wait a moment
        await asyncio.sleep(1)
        
        print("Session generation test completed successfully!")
        
        app.quit()
        
    except Exception as e:
        print(f"Error testing session: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

def main():
    """Main entry point"""
    try:
        result = asyncio.run(test_session_creation())
        return 0 if result else 1
    except Exception as e:
        print(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)