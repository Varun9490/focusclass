#!/usr/bin/env python3
"""
Debug test script for teacher application
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
    
    print("Starting teacher application debug test...")
    
    try:
        window = TeacherMainWindow()
        
        # Debug the UI creation
        print("Checking UI components...")
        
        # Check if left panel exists
        left_panel = window.create_left_panel()
        print(f"Left panel created: {left_panel is not None}")
        if left_panel:
            print(f"Left panel type: {type(left_panel)}")
        
        # Check if right panel exists  
        right_panel = window.create_right_panel()
        print(f"Right panel created: {right_panel is not None}")
        if right_panel:
            print(f"Right panel type: {type(right_panel)}")
        
        window.show()
        print("Teacher application window created and shown successfully!")
        print("Window title:", window.windowTitle())
        print("Window size:", window.size().width(), "x", window.size().height())
        
        # Check central widget
        central = window.centralWidget()
        print(f"Central widget: {central is not None}")
        if central:
            layout = central.layout()
            print(f"Central layout: {layout is not None}")
            if layout:
                print(f"Layout type: {type(layout)}")
                print(f"Layout item count: {layout.count()}")
        
        # Just show for a moment and close
        app.processEvents()
        print("UI debug test completed!")
        
    except Exception as e:
        print(f"Error creating teacher window: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)