#!/usr/bin/env python3
"""
Test script for teacher application
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication
from teacher.teacher_app import TeacherMainWindow

def main():
    app = QApplication(sys.argv)
    
    print("Starting teacher application test...")
    
    try:
        window = TeacherMainWindow()
        window.show()
        print("Teacher application window created and shown successfully!")
        print("Window title:", window.windowTitle())
        print("Window size:", window.size().width(), "x", window.size().height())
        
        # Just show for a moment and close
        app.processEvents()
        print("UI layout test completed successfully!")
        
    except Exception as e:
        print(f"Error creating teacher window: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)