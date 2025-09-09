#!/usr/bin/env python3
"""
Test student connection and screen sharing
"""

import sys
import asyncio
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication, QDialog
import qasync
from student.student_app import StudentMainWindow

async def test_student_connection():
    """Test student connection and screen sharing"""
    print("Testing student connection...")
    
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    try:
        # Create student window
        window = StudentMainWindow()
        
        # Simulate connection data (you'll need to update with actual session info)
        connection_data = {
            "teacher_ip": "172.168.20.113",
            "session_code": "ORQVIU_RUSM",  # Update this with actual session code
            "password": "DUIKXNCF04g3zP3h",  # Update this with actual password
            "student_name": "Test Student"
        }
        
        print(f"Connecting to teacher at {connection_data['teacher_ip']}...")
        print(f"Session: {connection_data['session_code']}")
        
        # Connect to teacher
        await window._connect_to_teacher_async(connection_data)
        
        if window.connected:
            print("✅ Connected successfully!")
            
            # Show window
            window.show()
            
            print("Waiting for teacher to start screen sharing...")
            print("You can now start screen sharing from the teacher app")
            print("Student app will display frames when received")
            
            # Wait for some time to see screen sharing in action
            await asyncio.sleep(30)
            
        else:
            print("❌ Connection failed")
            
        app.quit()
        
    except Exception as e:
        print(f"Error testing student connection: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

def main():
    """Main entry point"""
    try:
        result = asyncio.run(test_student_connection())
        return 0 if result else 1
    except Exception as e:
        print(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)