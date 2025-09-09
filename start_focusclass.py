#!/usr/bin/env python3
"""
Production startup script for FocusClass
Ensures all required directories exist and handles dependency checking
"""

import sys
import os
from pathlib import Path
import logging

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def setup_directories():
    """Ensure all required directories exist"""
    directories = [
        "assets",
        "logs",
        "exports",
        "temp"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory exists: {directory}")

def check_dependencies():
    """Check if critical dependencies are available"""
    try:
        import PyQt5
        print("✓ PyQt5 available")
    except ImportError:
        print("✗ PyQt5 not available - this is required")
        return False
    
    try:
        import websockets
        print("✓ websockets available")
    except ImportError:
        print("✗ websockets not available - this is required")
        return False
    
    try:
        import aiohttp
        print("✓ aiohttp available")
    except ImportError:
        print("✗ aiohttp not available - this is required")
        return False
    
    # Optional dependencies
    try:
        import qasync
        print("✓ qasync available")
    except ImportError:
        print("⚠ qasync not available - async GUI may not work properly")
    
    try:
        import mss
        print("✓ mss available")
    except ImportError:
        print("⚠ mss not available - screen capture may not work")
    
    try:
        import psutil
        print("✓ psutil available")
    except ImportError:
        print("⚠ psutil not available - system monitoring may not work")
    
    return True

def main():
    """Main startup function"""
    print("FocusClass Production Startup")
    print("=" * 40)
    
    # Setup directories
    print("\nSetting up directories...")
    setup_directories()
    
    # Check dependencies
    print("\nChecking dependencies...")
    if not check_dependencies():
        print("\nCritical dependencies missing. Please install them first.")
        return 1
    
    print("\nStarting FocusClass...")
    
    try:
        # Import and start the main launcher
        from focusclass_launcher import main as launcher_main
        return launcher_main()
        
    except ImportError:
        print("Error: Could not import FocusClass launcher")
        print("Trying to start teacher app directly...")
        
        try:
            from teacher.teacher_app import TeacherMainWindow
            from PyQt5.QtWidgets import QApplication
            import qasync
            import asyncio
            
            app = QApplication(sys.argv)
            loop = qasync.QEventLoop(app)
            asyncio.set_event_loop(loop)
            
            window = TeacherMainWindow()
            window.show()
            
            with loop:
                loop.run_forever()
                
        except Exception as e:
            print(f"Error starting teacher app: {e}")
            return 1
    
    except Exception as e:
        print(f"Error starting FocusClass: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)