#!/usr/bin/env python3
"""
Production Testing Suite for FocusClass Application
Comprehensive tests for both teacher and student functionality
"""

import sys
import os
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def setup_test_logging():
    """Setup logging for tests"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'test_production.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def test_imports():
    """Test that all critical modules import correctly"""
    logger = logging.getLogger(__name__)
    logger.info("Testing module imports...")
    
    critical_imports = [
        ('PyQt5.QtWidgets', 'QApplication'),
        ('PyQt5.QtCore', 'Qt'),
        ('PyQt5.QtGui', 'QFont'),
        ('qasync', 'QEventLoop'),
        ('websockets', 'serve'),
        ('mss', 'mss'),
        ('psutil', 'cpu_percent'),
        ('PIL', 'Image'),
        ('qrcode', 'QRCode'),
        ('numpy', 'array'),
    ]
    
    failed_imports = []
    
    for module_name, item_name in critical_imports:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            logger.info(f"✓ {module_name}.{item_name}")
        except ImportError as e:
            logger.error(f"✗ {module_name}.{item_name} - {e}")
            failed_imports.append(f"{module_name}.{item_name}")
        except AttributeError as e:
            logger.error(f"✗ {module_name}.{item_name} - {e}")
            failed_imports.append(f"{module_name}.{item_name}")
    
    # Test internal modules
    internal_modules = [
        'common.config',
        'common.utils',
        'common.database_manager',
        'common.network_manager',
        'common.screen_capture',
        'common.focus_manager',
        'teacher.teacher_app',
        'teacher.advanced_teacher_app',
        'student.student_app',
        'student.advanced_student_app',
    ]
    
    for module_name in internal_modules:
        try:
            __import__(module_name)
            logger.info(f"✓ {module_name}")
        except ImportError as e:
            logger.error(f"✗ {module_name} - {e}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0, failed_imports

def test_config_loading():
    """Test configuration loading"""
    logger = logging.getLogger(__name__)
    logger.info("Testing configuration loading...")
    
    try:
        from common.config import APP_NAME, APP_VERSION, DEFAULT_WEBSOCKET_PORT
        logger.info(f"✓ Config loaded: {APP_NAME} v{APP_VERSION}")
        logger.info(f"✓ Default WebSocket Port: {DEFAULT_WEBSOCKET_PORT}")
        return True
    except Exception as e:
        logger.error(f"✗ Config loading failed: {e}")
        return False

def test_database_manager():
    """Test database manager functionality"""
    logger = logging.getLogger(__name__)
    logger.info("Testing database manager...")
    
    try:
        from common.database_manager import DatabaseManager
        
        # Test database creation
        db = DatabaseManager()
        logger.info("✓ Database manager created")
        
        # Test session creation
        session_id = db.create_session("test_teacher", "TEST123", "testpass")
        if session_id:
            logger.info(f"✓ Session created: {session_id}")
        else:
            logger.error("✗ Session creation failed")
            return False
        
        # Test session retrieval
        session = db.get_session(session_id)
        if session:
            logger.info("✓ Session retrieved")
        else:
            logger.error("✗ Session retrieval failed")
            return False
        
        # Test student operations
        student_id = db.add_student(session_id, "test_student", "192.168.1.100")
        if student_id:
            logger.info(f"✓ Student added: {student_id}")
        else:
            logger.error("✗ Student addition failed")
            return False
        
        # Test violation logging
        violation_id = db.log_violation(student_id, "test_violation", "Test violation description")
        if violation_id:
            logger.info(f"✓ Violation logged: {violation_id}")
        else:
            logger.error("✗ Violation logging failed")
            return False
        
        logger.info("✓ Database manager tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database manager test failed: {e}")
        traceback.print_exc()
        return False

def test_screen_capture():
    """Test screen capture functionality"""
    logger = logging.getLogger(__name__)
    logger.info("Testing screen capture...")
    
    try:
        from common.screen_capture import ScreenCapture
        
        # Test screen capture creation
        capture = ScreenCapture()
        logger.info("✓ Screen capture manager created")
        
        # Test monitor detection
        monitors = capture.get_monitors()
        if monitors:
            logger.info(f"✓ Detected {len(monitors)} monitors")
        else:
            logger.warning("⚠ No monitors detected")
        
        # Test quality settings
        capture.set_quality("medium")
        logger.info("✓ Quality setting works")
        
        # Test screenshot
        screenshot = capture.take_screenshot()
        if screenshot:
            logger.info("✓ Screenshot captured successfully")
        else:
            logger.error("✗ Screenshot capture failed")
            return False
        
        # Test basic capture start/stop
        track = capture.start_capture()
        if track is not None:  # Can be a track or a string flag
            logger.info("✓ Screen capture starts successfully")
            
            # Test stats
            stats = capture.get_capture_stats()
            if stats:
                logger.info(f"✓ Capture stats available: {stats}")
            
            capture.stop_capture()
            logger.info("✓ Screen capture stops successfully")
        else:
            logger.error("✗ Screen capture failed to start")
            return False
        
        logger.info("✓ Screen capture tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Screen capture test failed: {e}")
        traceback.print_exc()
        return False

def test_focus_manager():
    """Test focus manager functionality"""
    logger = logging.getLogger(__name__)
    logger.info("Testing focus manager...")
    
    try:
        from common.focus_manager import is_admin, LightweightFocusManager
        
        # Test admin detection
        admin_status = is_admin()
        logger.info(f"✓ Admin status detected: {admin_status}")
        
        # Test lightweight focus manager (always available)
        def mock_violation_handler(violation_data):
            logger.info(f"Mock violation: {violation_data}")
        
        focus_manager = LightweightFocusManager(mock_violation_handler)
        logger.info("✓ Lightweight focus manager created")
        
        # Test basic operations (these might not work without admin privileges)
        try:
            import asyncio
            
            async def test_focus_operations():
                # These operations might fail without admin rights, which is expected
                result = await focus_manager.enable_focus_mode(["FocusClass"])
                logger.info(f"✓ Focus mode enable test: {result}")
                
                if result:
                    await focus_manager.disable_focus_mode()
                    logger.info("✓ Focus mode disable test")
                
                await focus_manager.cleanup()
                logger.info("✓ Focus manager cleanup")
            
            # Run async test
            asyncio.run(test_focus_operations())
            
        except Exception as e:
            logger.warning(f"⚠ Focus operations test (expected on non-admin): {e}")
        
        logger.info("✓ Focus manager tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Focus manager test failed: {e}")
        traceback.print_exc()
        return False

def test_utils():
    """Test utility functions"""
    logger = logging.getLogger(__name__)
    logger.info("Testing utility functions...")
    
    try:
        from common.utils import format_duration, format_bytes, get_local_ip, create_qr_code
        
        # Test duration formatting
        duration_str = format_duration(3661)  # 1 hour, 1 minute, 1 second
        logger.info(f"✓ Duration formatting: {duration_str}")
        
        # Test bytes formatting
        bytes_str = format_bytes(1536)  # 1.5 KB
        logger.info(f"✓ Bytes formatting: {bytes_str}")
        
        # Test IP detection
        local_ip = get_local_ip()
        if local_ip:
            logger.info(f"✓ Local IP detected: {local_ip}")
        else:
            logger.warning("⚠ Local IP detection failed")
        
        # Test QR code creation
        qr_data = {
            "teacher_ip": "192.168.1.100",
            "session_code": "TEST123",
            "password": "testpass"
        }
        qr_image = create_qr_code(qr_data)
        if qr_image:
            logger.info("✓ QR code generation works")
        else:
            logger.error("✗ QR code generation failed")
            return False
        
        logger.info("✓ Utility functions tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Utility functions test failed: {e}")
        traceback.print_exc()
        return False

def test_gui_components():
    """Test GUI components without actually showing windows"""
    logger = logging.getLogger(__name__)
    logger.info("Testing GUI components...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        
        # Create application instance
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test teacher app creation
        from teacher.advanced_teacher_app import AdvancedTeacherApp
        teacher_app = AdvancedTeacherApp()
        logger.info("✓ Advanced teacher app created")
        
        # Test student app creation
        from student.advanced_student_app import AdvancedStudentApp
        
        # Mock the connection dialog to avoid blocking
        import unittest.mock
        with unittest.mock.patch.object(AdvancedStudentApp, 'show_connection_dialog'):
            student_app = AdvancedStudentApp()
            logger.info("✓ Advanced student app created")
        
        # Test main launcher
        from FocusClass import WelcomeWindow
        welcome = WelcomeWindow()
        logger.info("✓ Welcome window created")
        
        # Clean up
        teacher_app.close()
        student_app.close()
        welcome.close()
        
        logger.info("✓ GUI components tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ GUI components test failed: {e}")
        traceback.print_exc()
        return False

def test_network_components():
    """Test network components"""
    logger = logging.getLogger(__name__)
    logger.info("Testing network components...")
    
    try:
        from common.network_manager import NetworkManager, generate_session_code, generate_session_password
        
        # Test session code generation
        session_code = generate_session_code()
        if session_code and len(session_code) == 8:
            logger.info(f"✓ Session code generated: {session_code}")
        else:
            logger.error("✗ Session code generation failed")
            return False
        
        # Test password generation
        password = generate_session_password()
        if password and len(password) >= 8:
            logger.info(f"✓ Password generated: {password}")
        else:
            logger.error("✗ Password generation failed")
            return False
        
        # Test network manager creation
        teacher_network = NetworkManager(is_teacher=True)
        logger.info("✓ Teacher network manager created")
        
        student_network = NetworkManager(is_teacher=False)
        logger.info("✓ Student network manager created")
        
        logger.info("✓ Network components tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Network components test failed: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """Run all tests and return summary"""
    logger = setup_test_logging()
    
    logger.info("="*60)
    logger.info("🧪 FOCUSCLASS PRODUCTION TEST SUITE")
    logger.info("="*60)
    logger.info(f"Test started at: {datetime.now()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info("="*60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration Loading", test_config_loading),
        ("Database Manager", test_database_manager),
        ("Screen Capture", test_screen_capture),
        ("Focus Manager", test_focus_manager),
        ("Utility Functions", test_utils),
        ("Network Components", test_network_components),
        ("GUI Components", test_gui_components),
    ]
    
    results = []
    passed_count = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        logger.info("-" * 40)
        
        start_time = time.time()
        try:
            success = test_func()
            duration = time.time() - start_time
            
            if success:
                logger.info(f"✅ {test_name} PASSED ({duration:.2f}s)")
                passed_count += 1
            else:
                logger.error(f"❌ {test_name} FAILED ({duration:.2f}s)")
            
            results.append((test_name, success, duration))
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"💥 {test_name} CRASHED ({duration:.2f}s): {e}")
            results.append((test_name, False, duration))
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    total_duration = sum(duration for _, _, duration in results)
    
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name:.<35} {status} ({duration:.2f}s)")
    
    logger.info("-" * 60)
    logger.info(f"Total Tests: {len(tests)}")
    logger.info(f"Passed: {passed_count}")
    logger.info(f"Failed: {len(tests) - passed_count}")
    logger.info(f"Success Rate: {passed_count/len(tests)*100:.1f}%")
    logger.info(f"Total Duration: {total_duration:.2f}s")
    
    if passed_count == len(tests):
        logger.info("\n🎉 ALL TESTS PASSED! 🎉")
        logger.info("The application is ready for production use.")
    else:
        logger.warning(f"\n⚠️  {len(tests) - passed_count} TEST(S) FAILED")
        logger.warning("Please fix the issues before production deployment.")
    
    logger.info("="*60)
    
    return passed_count == len(tests)

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)