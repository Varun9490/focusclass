"""
Focus Manager for FocusClass Application
Handles Windows restrictions and focus mode enforcement
"""

import asyncio
import logging
import time
import threading
from typing import Callable, List, Optional, Dict, Any
import sys

# Windows-specific imports
if sys.platform == "win32":
    import win32api
    import win32con
    import win32gui
    import win32process
    import win32security
    import win32service
    import win32serviceutil
    import pywintypes
    import ctypes
    from ctypes import wintypes
    import psutil
    import winreg


class FocusManager:
    """Manages focus mode restrictions on Windows"""
    
    def __init__(self, violation_callback: Optional[Callable] = None):
        """
        Initialize focus manager
        
        Args:
            violation_callback: Function to call when violations are detected
        """
        self.logger = logging.getLogger(__name__)
        self.violation_callback = violation_callback
        
        # Focus mode state
        self.focus_mode_active = False
        self.allowed_windows = set()
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
        # Violation tracking
        self.violation_count = 0
        self.last_violation_time = 0
        
        # Windows API components
        self.hook_manager = None
        self.keyboard_hook = None
        self.window_hook = None
        
        # Original Windows settings (for restoration)
        self.original_settings = {}
        
        # Restricted key combinations
        self.restricted_keys = {
            'alt_tab': [win32con.VK_MENU, win32con.VK_TAB],
            'win_key': [win32con.VK_LWIN, win32con.VK_RWIN],
            'ctrl_esc': [win32con.VK_CONTROL, win32con.VK_ESCAPE],
            'ctrl_shift_esc': [win32con.VK_CONTROL, win32con.VK_SHIFT, win32con.VK_ESCAPE],
            'alt_f4': [win32con.VK_MENU, win32con.VK_F4],
            'ctrl_alt_del': [win32con.VK_CONTROL, win32con.VK_MENU, win32con.VK_DELETE]
        }
        
        # Currently pressed keys
        self.pressed_keys = set()
        
        if sys.platform != "win32":
            self.logger.warning("Focus Manager only works on Windows")
    
    def is_windows(self) -> bool:
        """Check if running on Windows"""
        return sys.platform == "win32"
    
    async def enable_focus_mode(self, allowed_window_titles: List[str] = None) -> bool:
        """
        Enable focus mode with restrictions
        
        Args:
            allowed_window_titles: List of window titles that are allowed to be active
            
        Returns:
            Success status
        """
        if not self.is_windows():
            self.logger.error("Focus mode only supported on Windows")
            return False
        
        try:
            self.focus_mode_active = True
            self.allowed_windows = set(allowed_window_titles or ["FocusClass Student"])
            
            # Install keyboard hooks
            await self._install_keyboard_hook()
            
            # Install window hooks
            await self._install_window_hook()
            
            # Configure Windows Focus Assist
            await self._enable_focus_assist()
            
            # Disable task switching
            await self._disable_task_switching()
            
            # Start monitoring thread
            self._start_monitoring()
            
            self.logger.info("Focus mode enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable focus mode: {e}")
            await self.disable_focus_mode()
            return False
    
    async def disable_focus_mode(self) -> bool:
        """
        Disable focus mode and restore normal functionality
        
        Returns:
            Success status
        """
        if not self.is_windows():
            return True
        
        try:
            self.focus_mode_active = False
            
            # Stop monitoring
            self._stop_monitoring()
            
            # Remove hooks
            await self._remove_keyboard_hook()
            await self._remove_window_hook()
            
            # Restore Windows settings
            await self._restore_windows_settings()
            
            # Disable Focus Assist
            await self._disable_focus_assist()
            
            self.logger.info("Focus mode disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling focus mode: {e}")
            return False
    
    async def _install_keyboard_hook(self):
        """Install low-level keyboard hook"""
        try:
            # Define hook procedure
            def keyboard_hook_proc(nCode, wParam, lParam):
                if nCode >= 0:
                    if wParam in [win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN]:
                        vk_code = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_int)).contents.value
                        self.pressed_keys.add(vk_code)
                        
                        # Check for restricted key combinations
                        if self._check_restricted_keys():
                            self._log_violation("keyboard", f"Restricted key combination detected")
                            return 1  # Block the key
                    
                    elif wParam in [win32con.WM_KEYUP, win32con.WM_SYSKEYUP]:
                        vk_code = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_int)).contents.value
                        self.pressed_keys.discard(vk_code)
                
                return ctypes.windll.user32.CallNextHookExW(self.keyboard_hook, nCode, wParam, lParam)
            
            # Install hook
            hook_id = win32gui.SetWindowsHookEx(
                win32con.WH_KEYBOARD_LL,
                keyboard_hook_proc,
                win32api.GetModuleHandle(None),
                0
            )
            
            self.keyboard_hook = hook_id
            self.logger.info("Keyboard hook installed")
            
        except Exception as e:
            self.logger.error(f"Failed to install keyboard hook: {e}")
    
    async def _remove_keyboard_hook(self):
        """Remove keyboard hook"""
        try:
            if self.keyboard_hook:
                win32gui.UnhookWindowsHookEx(self.keyboard_hook)
                self.keyboard_hook = None
                self.logger.info("Keyboard hook removed")
        except Exception as e:
            self.logger.error(f"Error removing keyboard hook: {e}")
    
    async def _install_window_hook(self):
        """Install window event hook"""
        try:
            def window_hook_proc(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
                if event == win32con.EVENT_SYSTEM_FOREGROUND:
                    try:
                        window_title = win32gui.GetWindowText(hwnd)
                        if window_title and not self._is_window_allowed(window_title):
                            self._log_violation("window_switch", f"Switched to unauthorized window: {window_title}")
                            
                            # Try to bring allowed window back to focus
                            self._focus_allowed_window()
                            
                    except Exception as e:
                        self.logger.error(f"Error in window hook: {e}")
            
            # Install window event hook
            self.window_hook = win32gui.SetWinEventHook(
                win32con.EVENT_SYSTEM_FOREGROUND,
                win32con.EVENT_SYSTEM_FOREGROUND,
                0,
                window_hook_proc,
                0,
                0,
                win32con.WINEVENT_OUTOFCONTEXT
            )
            
            self.logger.info("Window hook installed")
            
        except Exception as e:
            self.logger.error(f"Failed to install window hook: {e}")
    
    async def _remove_window_hook(self):
        """Remove window hook"""
        try:
            if self.window_hook:
                win32gui.UnhookWinEventHook(self.window_hook)
                self.window_hook = None
                self.logger.info("Window hook removed")
        except Exception as e:
            self.logger.error(f"Error removing window hook: {e}")
    
    def _check_restricted_keys(self) -> bool:
        """Check if current key combination is restricted"""
        for combo_name, keys in self.restricted_keys.items():
            if all(key in self.pressed_keys for key in keys):
                return True
        return False
    
    def _is_window_allowed(self, window_title: str) -> bool:
        """Check if window is allowed in focus mode"""
        if not self.focus_mode_active:
            return True
        
        # Check against allowed window titles
        for allowed in self.allowed_windows:
            if allowed.lower() in window_title.lower():
                return True
        
        # Always allow system windows
        system_windows = [
            "Program Manager",
            "Desktop Window Manager",
            "Windows Security",
            "Task Manager"
        ]
        
        for system_window in system_windows:
            if system_window.lower() in window_title.lower():
                return True
        
        return False
    
    def _focus_allowed_window(self):
        """Bring an allowed window to focus"""
        try:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if self._is_window_allowed(window_title):
                        windows.append((hwnd, window_title))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                # Focus the first allowed window
                hwnd, title = windows[0]
                win32gui.SetForegroundWindow(hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                self.logger.info(f"Refocused to allowed window: {title}")
            
        except Exception as e:
            self.logger.error(f"Error focusing allowed window: {e}")
    
    async def _enable_focus_assist(self):
        """Enable Windows Focus Assist to block notifications"""
        try:
            # Save current Focus Assist state
            registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_READ) as key:
                try:
                    current_value = winreg.QueryValueEx(key, "Current")[0]
                    self.original_settings['focus_assist'] = current_value
                except FileNotFoundError:
                    self.original_settings['focus_assist'] = None
            
            # Enable Focus Assist (Priority only mode)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "Current", 0, winreg.REG_DWORD, 1)
            
            self.logger.info("Focus Assist enabled")
            
        except Exception as e:
            self.logger.error(f"Failed to enable Focus Assist: {e}")
    
    async def _disable_focus_assist(self):
        """Restore original Focus Assist settings"""
        try:
            if 'focus_assist' in self.original_settings:
                registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount"
                
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_WRITE) as key:
                    if self.original_settings['focus_assist'] is not None:
                        winreg.SetValueEx(key, "Current", 0, winreg.REG_DWORD, 
                                        self.original_settings['focus_assist'])
                    else:
                        try:
                            winreg.DeleteValue(key, "Current")
                        except FileNotFoundError:
                            pass
                
                self.logger.info("Focus Assist settings restored")
                
        except Exception as e:
            self.logger.error(f"Failed to restore Focus Assist: {e}")
    
    async def _disable_task_switching(self):
        """Disable task switching mechanisms"""
        try:
            # Disable Alt+Tab task switcher
            # This is achieved through the keyboard hook
            
            # Hide taskbar (optional - might be too restrictive)
            # taskbar = win32gui.FindWindow("Shell_TrayWnd", None)
            # if taskbar:
            #     win32gui.ShowWindow(taskbar, win32con.SW_HIDE)
            #     self.original_settings['taskbar_visible'] = True
            
            self.logger.info("Task switching restrictions applied")
            
        except Exception as e:
            self.logger.error(f"Failed to disable task switching: {e}")
    
    async def _restore_windows_settings(self):
        """Restore original Windows settings"""
        try:
            # Restore taskbar if hidden
            if self.original_settings.get('taskbar_visible'):
                taskbar = win32gui.FindWindow("Shell_TrayWnd", None)
                if taskbar:
                    win32gui.ShowWindow(taskbar, win32con.SW_SHOW)
            
            self.logger.info("Windows settings restored")
            
        except Exception as e:
            self.logger.error(f"Failed to restore Windows settings: {e}")
    
    def _start_monitoring(self):
        """Start monitoring thread for additional checks"""
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Monitoring thread started")
    
    def _stop_monitoring(self):
        """Stop monitoring thread"""
        if self.monitoring_thread:
            self.stop_monitoring.set()
            self.monitoring_thread.join(timeout=5)
            self.monitoring_thread = None
            self.logger.info("Monitoring thread stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self.stop_monitoring.is_set():
            try:
                if self.focus_mode_active:
                    # Check for unauthorized processes
                    self._check_unauthorized_processes()
                    
                    # Check window focus
                    self._check_window_focus()
                    
                    # Check for screen recording software
                    self._check_screen_recording()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _check_unauthorized_processes(self):
        """Check for unauthorized processes"""
        try:
            # List of processes that should be blocked during focus mode
            blocked_processes = [
                "taskmgr.exe",      # Task Manager
                "cmd.exe",          # Command Prompt
                "powershell.exe",   # PowerShell
                "regedit.exe",      # Registry Editor
                "msconfig.exe",     # System Configuration
                "control.exe",      # Control Panel
            ]
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() in [p.lower() for p in blocked_processes]:
                        self._log_violation("unauthorized_process", 
                                          f"Unauthorized process detected: {proc.info['name']}")
                        
                        # Optionally terminate the process
                        # proc.terminate()
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error checking processes: {e}")
    
    def _check_window_focus(self):
        """Check current window focus"""
        try:
            foreground_window = win32gui.GetForegroundWindow()
            if foreground_window:
                window_title = win32gui.GetWindowText(foreground_window)
                
                if window_title and not self._is_window_allowed(window_title):
                    # This violation is already logged by the window hook
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error checking window focus: {e}")
    
    def _check_screen_recording(self):
        """Check for screen recording software"""
        try:
            # List of common screen recording software
            recording_software = [
                "obs64.exe",        # OBS Studio
                "obs32.exe",
                "bandicam.exe",     # Bandicam
                "camtasia.exe",     # Camtasia
                "fraps.exe",        # Fraps
                "screenrec.exe",    # Various screen recorders
            ]
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() in [p.lower() for p in recording_software]:
                        self._log_violation("screen_recording", 
                                          f"Screen recording software detected: {proc.info['name']}")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error checking screen recording: {e}")
    
    def _log_violation(self, violation_type: str, description: str):
        """Log a focus mode violation"""
        current_time = time.time()
        
        # Avoid spam by limiting violations
        if current_time - self.last_violation_time < 1:  # 1 second cooldown
            return
        
        self.last_violation_time = current_time
        self.violation_count += 1
        
        violation_data = {
            "type": violation_type,
            "description": description,
            "timestamp": current_time,
            "count": self.violation_count
        }
        
        self.logger.warning(f"Focus violation: {violation_type} - {description}")
        
        # Call violation callback if provided
        if self.violation_callback:
            try:
                asyncio.create_task(self.violation_callback(violation_data))
            except Exception as e:
                self.logger.error(f"Error in violation callback: {e}")
    
    # Public methods for external control
    def add_allowed_window(self, window_title: str):
        """Add a window to the allowed list"""
        self.allowed_windows.add(window_title)
        self.logger.info(f"Added allowed window: {window_title}")
    
    def remove_allowed_window(self, window_title: str):
        """Remove a window from the allowed list"""
        self.allowed_windows.discard(window_title)
        self.logger.info(f"Removed allowed window: {window_title}")
    
    def get_violation_count(self) -> int:
        """Get current violation count"""
        return self.violation_count
    
    def reset_violation_count(self):
        """Reset violation count"""
        self.violation_count = 0
        self.logger.info("Violation count reset")
    
    def is_focus_mode_active(self) -> bool:
        """Check if focus mode is currently active"""
        return self.focus_mode_active
    
    # Utility methods
    def get_current_window_title(self) -> str:
        """Get title of currently focused window"""
        try:
            if self.is_windows():
                foreground_window = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(foreground_window)
            return ""
        except Exception:
            return ""
    
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of currently running processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error getting processes: {e}")
        
        return processes
    
    async def cleanup(self):
        """Clean up resources"""
        await self.disable_focus_mode()
        self.logger.info("Focus manager cleaned up")


# Helper functions
def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin_privileges():
    """Request administrator privileges"""
    if not is_admin():
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return False
    return True


class LightweightFocusManager:
    """Lightweight focus manager for systems without admin privileges"""
    
    def __init__(self, violation_callback: Optional[Callable] = None):
        self.logger = logging.getLogger(__name__)
        self.violation_callback = violation_callback
        self.focus_mode_active = False
        self.allowed_windows = set()
        
    async def enable_focus_mode(self, allowed_window_titles: List[str] = None) -> bool:
        """Enable lightweight focus mode"""
        self.focus_mode_active = True
        self.allowed_windows = set(allowed_window_titles or ["FocusClass Student"])
        
        # Only basic window monitoring without hooks
        asyncio.create_task(self._monitor_windows())
        
        self.logger.info("Lightweight focus mode enabled")
        return True
    
    async def disable_focus_mode(self) -> bool:
        """Disable lightweight focus mode"""
        self.focus_mode_active = False
        self.logger.info("Lightweight focus mode disabled")
        return True
    
    async def _monitor_windows(self):
        """Monitor windows without hooks"""
        while self.focus_mode_active:
            try:
                if sys.platform == "win32":
                    foreground_window = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(foreground_window)
                    
                    if window_title and not self._is_window_allowed(window_title):
                        await self._log_violation("window_switch", 
                                                f"Switched to unauthorized window: {window_title}")
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring windows: {e}")
                await asyncio.sleep(5)
    
    def _is_window_allowed(self, window_title: str) -> bool:
        """Check if window is allowed"""
        for allowed in self.allowed_windows:
            if allowed.lower() in window_title.lower():
                return True
        return False
    
    async def _log_violation(self, violation_type: str, description: str):
        """Log violation"""
        if self.violation_callback:
            await self.violation_callback({
                "type": violation_type,
                "description": description,
                "timestamp": time.time()
            })
    
    def is_focus_mode_active(self) -> bool:
        return self.focus_mode_active
    
    async def cleanup(self):
        await self.disable_focus_mode()