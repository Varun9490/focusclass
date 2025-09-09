#!/usr/bin/env python3
"""
Test script for student application
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication
from student.student_app import StudentMainWindow

def main():
    app = QApplication(sys.argv)
    
    print("Starting student application test...")
    
    try:
        window = StudentMainWindow()
        window.show()
        print("Student application window created and shown successfully!")
        print("Window title:", window.windowTitle())
        print("Window size:", window.size().width(), "x", window.size().height())
        
        # Just show for a moment and close
        app.processEvents()
        print("Student app test completed successfully!")
        
    except Exception as e:
        print(f"Error creating student window: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)