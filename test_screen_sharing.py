#!/usr/bin/env python3
"""
Test screen sharing functionality
"""

import sys
import asyncio
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication
import qasync
from teacher.teacher_app import TeacherMainWindow

async def test_screen_sharing():
    """Test screen sharing functionality"""
    print("Testing screen sharing...")
    
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    try:
        window = TeacherMainWindow()
        window.show()
        
        print("Starting session...")
        await window._start_session_async()
        
        print("Session started, testing screen sharing...")
        
        # Test screen sharing
        await window._start_screen_sharing_async(0, "medium")
        
        print("Screen sharing started, capturing some frames...")
        
        # Let it capture a few frames
        for i in range(5):
            await asyncio.sleep(1)
            window.capture_and_send_frame()
            print(f"Frame {i+1} captured and sent")
        
        print("Screen sharing test completed!")
        
        # Stop sharing
        await window._stop_screen_sharing_async()
        print("Screen sharing stopped")
        
        app.quit()
        
    except Exception as e:
        print(f"Error testing screen sharing: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

def main():
    """Main entry point"""
    try:
        result = asyncio.run(test_screen_sharing())
        return 0 if result else 1
    except Exception as e:
        print(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)