"""
Screen Capture Manager for FocusClass Application
Handles screen recording, streaming, and WebRTC media tracks
"""

import asyncio
import logging
import threading
import time
from typing import Optional, Callable, Tuple, List
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Optional OpenCV import
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: cv2 not available. Some advanced features may be disabled.")

# Screen capture
import mss
try:
    import pyautogui
except ImportError:
    pyautogui = None
    print("Warning: pyautogui not available.")

# WebRTC imports with fallbacks
try:
    from aiortc import MediaStreamTrack, VideoStreamTrack
    from aiortc.contrib.media import MediaPlayer
    from av import VideoFrame
    import fractions
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    print("Warning: aiortc/av not available. WebRTC screen sharing will be disabled.")
    
    # Create dummy classes for compatibility
    class VideoStreamTrack:
        kind = "video"
        def __init__(self): pass
        async def recv(self): return None
    
    class MediaStreamTrack:
        def __init__(self): pass
    
    class VideoFrame:
        @staticmethod
        def from_ndarray(array, format): return None
    
    class MediaPlayer:
        def __init__(self, *args, **kwargs): pass
    
    import fractions


class ScreenCaptureTrack(VideoStreamTrack):
    """Custom video track for screen capture"""
    
    kind = "video"
    
    def __init__(self, monitor: int = 0, fps: int = 15, scale_factor: float = 1.0):
        """
        Initialize screen capture track
        
        Args:
            monitor: Monitor number to capture (0 = primary)
            fps: Frames per second
            scale_factor: Scale factor for resolution (1.0 = original size)
        """
        if WEBRTC_AVAILABLE:
            super().__init__()
        
        self.monitor = monitor
        self.fps = fps
        self.scale_factor = scale_factor
        self.logger = logging.getLogger(__name__)
        
        # Screen capture setup
        self.sct = mss.mss()
        self.monitor_info = self.sct.monitors[monitor + 1]  # 0 is all monitors
        
        # Calculate scaled dimensions
        self.width = int(self.monitor_info["width"] * scale_factor)
        self.height = int(self.monitor_info["height"] * scale_factor)
        
        # Frame timing
        self.frame_duration = 1.0 / fps
        self.last_frame_time = 0
        
        # Performance tracking
        self.frame_count = 0
        self.capture_times = []
        
        self.logger.info(f"Screen capture initialized: {self.width}x{self.height} @ {fps}fps")
    
    async def recv(self):
        """Receive next video frame"""
        if not WEBRTC_AVAILABLE:
            self.logger.warning("WebRTC not available. Cannot provide video frames.")
            await asyncio.sleep(1)  # Prevent tight loop
            return None
            
        # Control frame rate
        current_time = time.time()
        if current_time - self.last_frame_time < self.frame_duration:
            await asyncio.sleep(self.frame_duration - (current_time - self.last_frame_time))
        
        start_time = time.time()
        
        try:
            # Capture screen
            screenshot = self.sct.grab(self.monitor_info)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Scale if necessary
            if self.scale_factor != 1.0:
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Create VideoFrame
            if WEBRTC_AVAILABLE:
                frame = VideoFrame.from_ndarray(img_array, format="rgb24")
                frame.pts = self.frame_count
                frame.time_base = fractions.Fraction(1, self.fps)
            else:
                frame = None
            
            # Performance tracking
            capture_time = time.time() - start_time
            self.capture_times.append(capture_time)
            if len(self.capture_times) > 100:
                self.capture_times.pop(0)
            
            self.frame_count += 1
            self.last_frame_time = current_time
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")
            # Return a black frame on error
            if WEBRTC_AVAILABLE:
                black_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                frame = VideoFrame.from_ndarray(black_frame, format="rgb24")
                frame.pts = self.frame_count
                frame.time_base = fractions.Fraction(1, self.fps)
                self.frame_count += 1
                return frame
            else:
                return None
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics"""
        if not self.capture_times:
            return {}
        
        avg_capture_time = sum(self.capture_times) / len(self.capture_times)
        max_capture_time = max(self.capture_times)
        
        return {
            "avg_capture_time": avg_capture_time,
            "max_capture_time": max_capture_time,
            "actual_fps": 1.0 / avg_capture_time if avg_capture_time > 0 else 0,
            "frame_count": self.frame_count
        }


class ScreenCapture:
    """Main screen capture manager"""
    
    def __init__(self):
        """Initialize screen capture manager"""
        self.logger = logging.getLogger(__name__)
        
        # Capture state
        self.is_capturing = False
        self.capture_track = None
        
        # Available monitors
        self.monitors = []
        self._detect_monitors()
        
        # Capture settings
        self.current_monitor = 0
        self.fps = 15
        self.scale_factor = 1.0
        self.quality = "medium"
        
        # Quality presets
        self.quality_presets = {
            "low": {"fps": 10, "scale": 0.5},
            "medium": {"fps": 15, "scale": 0.75},
            "high": {"fps": 20, "scale": 1.0},
            "ultra": {"fps": 30, "scale": 1.0}
        }
        
        # Callbacks
        self.frame_callback = None
        
    def _detect_monitors(self):
        """Detect available monitors"""
        try:
            with mss.mss() as sct:
                self.monitors = sct.monitors[1:]  # Skip the "All monitors" entry
                
            self.logger.info(f"Detected {len(self.monitors)} monitors")
            for i, monitor in enumerate(self.monitors):
                self.logger.info(f"Monitor {i}: {monitor['width']}x{monitor['height']} "
                               f"at ({monitor['left']}, {monitor['top']})")
                
        except Exception as e:
            self.logger.error(f"Error detecting monitors: {e}")
            # Fallback to primary monitor
            self.monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]
    
    def get_monitors(self) -> List[dict]:
        """Get list of available monitors"""
        return self.monitors.copy()
    
    def set_quality(self, quality: str):
        """Set capture quality preset"""
        if quality in self.quality_presets:
            preset = self.quality_presets[quality]
            self.fps = preset["fps"]
            self.scale_factor = preset["scale"]
            self.quality = quality
            self.logger.info(f"Quality set to {quality}: {self.fps}fps, scale={self.scale_factor}")
        else:
            self.logger.warning(f"Unknown quality preset: {quality}")
    
    def set_custom_settings(self, fps: int, scale_factor: float):
        """Set custom capture settings"""
        self.fps = max(1, min(60, fps))  # Limit between 1-60 fps
        self.scale_factor = max(0.1, min(2.0, scale_factor))  # Limit scale factor
        self.quality = "custom"
        self.logger.info(f"Custom settings: {self.fps}fps, scale={self.scale_factor}")
    
    def start_capture(self, monitor: int = 0) -> Optional[ScreenCaptureTrack]:
        """
        Start screen capture
        
        Args:
            monitor: Monitor index to capture
            
        Returns:
            Screen capture track for WebRTC (or None if WebRTC unavailable)
        """
        if self.is_capturing:
            self.logger.warning("Screen capture already active")
            return self.capture_track
        
        if monitor >= len(self.monitors):
            self.logger.error(f"Monitor {monitor} not available")
            return None
            
        try:
            self.current_monitor = monitor
            
            if WEBRTC_AVAILABLE:
                # Full WebRTC mode
                self.capture_track = ScreenCaptureTrack(
                    monitor=monitor,
                    fps=self.fps,
                    scale_factor=self.scale_factor
                )
            else:
                # Fallback mode - create a basic capture system  
                self.logger.info("Starting basic screen capture mode (WebRTC unavailable)")
                self.capture_track = "basic_capture"  # Simple flag for basic mode
            
            self.is_capturing = True
            self.logger.info(f"Screen capture started for monitor {monitor} (mode: {'WebRTC' if WEBRTC_AVAILABLE else 'Basic'})")
            
            return self.capture_track
            
        except Exception as e:
            self.logger.error(f"Failed to start screen capture: {e}")
            return None
    
    def stop_capture(self):
        """Stop screen capture"""
        if not self.is_capturing:
            return
        
        self.is_capturing = False
        self.capture_track = None
        
        self.logger.info("Screen capture stopped")
    
    def take_screenshot(self, monitor: int = 0, save_path: Optional[str] = None) -> Optional[Image.Image]:
        """
        Take a single screenshot
        
        Args:
            monitor: Monitor index
            save_path: Optional path to save image
            
        Returns:
            PIL Image object
        """
        try:
            with mss.mss() as sct:
                if monitor >= len(self.monitors):
                    monitor = 0
                
                monitor_info = sct.monitors[monitor + 1]
                screenshot = sct.grab(monitor_info)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                if save_path:
                    img.save(save_path)
                    self.logger.info(f"Screenshot saved to {save_path}")
                
                return img
                
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return None
    
    def get_capture_stats(self) -> dict:
        """Get capture performance statistics"""
        if not self.is_capturing or not self.capture_track:
            return {}
        
        if WEBRTC_AVAILABLE and hasattr(self.capture_track, 'get_performance_stats'):
            stats = self.capture_track.get_performance_stats()
            stats.update({
                "monitor": self.current_monitor,
                "quality": self.quality,
                "target_fps": self.fps,
                "scale_factor": self.scale_factor
            })
            return stats
        else:
            # Basic stats for non-WebRTC mode
            return {
                "monitor": self.current_monitor,
                "quality": self.quality,
                "target_fps": self.fps,
                "scale_factor": self.scale_factor,
                "mode": "basic"
            }
    
    def capture_frame_data(self) -> Optional[bytes]:
        """Capture a single frame as bytes (fallback for non-WebRTC mode)"""
        try:
            if not self.is_capturing:
                return None
                
            screenshot = self.take_screenshot(self.current_monitor)
            if screenshot:
                # Convert to bytes
                buffer = io.BytesIO()
                screenshot.save(buffer, format="JPEG", quality=75)
                buffer.seek(0)
                return buffer.getvalue()
            return None
            
        except Exception as e:
            self.logger.error(f"Error capturing frame data: {e}")
            return None
    
    def register_frame_callback(self, callback: Callable):
        """Register callback for frame events"""
        self.frame_callback = callback


class StudentScreenShare:
    """Handles student screen sharing requests"""
    
    def __init__(self, approval_callback: Optional[Callable] = None):
        """
        Initialize student screen share
        
        Args:
            approval_callback: Function to call for approval requests
        """
        self.logger = logging.getLogger(__name__)
        self.approval_callback = approval_callback
        
        # Sharing state
        self.is_sharing = False
        self.share_track = None
        
        # Auto-approval settings
        self.auto_approve = False
        self.require_confirmation = True
        
        # Screen capture for sharing
        self.screen_capture = ScreenCapture()
    
    async def handle_share_request(self, request_data: dict) -> dict:
        """
        Handle screen share request from teacher
        
        Args:
            request_data: Request details
            
        Returns:
            Response data
        """
        try:
            if self.auto_approve and not self.require_confirmation:
                # Auto-approve without user interaction
                success = await self._start_sharing()
                return {
                    "success": success,
                    "message": "Screen sharing started automatically" if success else "Failed to start sharing"
                }
            
            # Request user approval
            if self.approval_callback:
                approved = await self.approval_callback(request_data)
                if approved:
                    success = await self._start_sharing()
                    return {
                        "success": success,
                        "message": "Screen sharing started" if success else "Failed to start sharing"
                    }
                else:
                    return {
                        "success": False,
                        "message": "Screen sharing denied by user"
                    }
            else:
                # No approval mechanism - deny by default
                return {
                    "success": False,
                    "message": "Screen sharing not configured"
                }
                
        except Exception as e:
            self.logger.error(f"Error handling share request: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def _start_sharing(self) -> bool:
        """Start screen sharing"""
        try:
            if self.is_sharing:
                self.logger.warning("Screen sharing already active")
                return True
            
            # Start screen capture with lower quality for sharing
            self.screen_capture.set_quality("medium")
            self.share_track = self.screen_capture.start_capture()
            
            if self.share_track:
                self.is_sharing = True
                self.logger.info("Student screen sharing started")
                return True
            else:
                self.logger.error("Failed to create share track")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting screen sharing: {e}")
            return False
    
    async def stop_sharing(self):
        """Stop screen sharing"""
        if not self.is_sharing:
            return
        
        try:
            self.screen_capture.stop_capture()
            self.share_track = None
            self.is_sharing = False
            
            self.logger.info("Student screen sharing stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping screen sharing: {e}")
    
    def get_share_track(self) -> Optional[ScreenCaptureTrack]:
        """Get the current share track for WebRTC"""
        return self.share_track if self.is_sharing else None
    
    def set_auto_approve(self, auto_approve: bool, require_confirmation: bool = True):
        """Set auto-approval settings"""
        self.auto_approve = auto_approve
        self.require_confirmation = require_confirmation
        
        self.logger.info(f"Auto-approve: {auto_approve}, Require confirmation: {require_confirmation}")


class ScreenAnnotation:
    """Handles screen annotations for teacher"""
    
    def __init__(self):
        """Initialize screen annotation"""
        self.logger = logging.getLogger(__name__)
        
        # Annotation state
        self.annotations = []
        self.annotation_overlay = None
        
        # Drawing settings
        self.pen_color = (255, 0, 0)  # Red
        self.pen_width = 3
        self.font_size = 24
        
    def add_annotation(self, annotation_type: str, position: Tuple[int, int], 
                      data: dict = None):
        """
        Add annotation to screen
        
        Args:
            annotation_type: Type of annotation (circle, arrow, text, etc.)
            position: (x, y) position
            data: Additional annotation data
        """
        annotation = {
            "type": annotation_type,
            "position": position,
            "data": data or {},
            "timestamp": time.time()
        }
        
        self.annotations.append(annotation)
        self.logger.debug(f"Added annotation: {annotation_type} at {position}")
    
    def clear_annotations(self):
        """Clear all annotations"""
        self.annotations.clear()
        self.annotation_overlay = None
        self.logger.info("Annotations cleared")
    
    def create_overlay(self, screen_size: Tuple[int, int]) -> Image.Image:
        """
        Create annotation overlay
        
        Args:
            screen_size: (width, height) of screen
            
        Returns:
            PIL Image with annotations
        """
        try:
            # Create transparent overlay
            overlay = Image.new("RGBA", screen_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Try to load a font
            try:
                font = ImageFont.truetype("arial.ttf", self.font_size)
            except:
                font = ImageFont.load_default()
            
            # Draw annotations
            for annotation in self.annotations:
                ann_type = annotation["type"]
                pos = annotation["position"]
                data = annotation["data"]
                
                if ann_type == "circle":
                    radius = data.get("radius", 20)
                    draw.ellipse([
                        pos[0] - radius, pos[1] - radius,
                        pos[0] + radius, pos[1] + radius
                    ], outline=self.pen_color, width=self.pen_width)
                
                elif ann_type == "arrow":
                    end_pos = data.get("end_position", (pos[0] + 50, pos[1]))
                    draw.line([pos, end_pos], fill=self.pen_color, width=self.pen_width)
                    
                    # Draw arrowhead
                    arrow_size = 10
                    dx = end_pos[0] - pos[0]
                    dy = end_pos[1] - pos[1]
                    length = (dx**2 + dy**2)**0.5
                    
                    if length > 0:
                        # Normalize direction
                        dx /= length
                        dy /= length
                        
                        # Arrow points
                        p1 = (end_pos[0] - arrow_size * dx + arrow_size * dy * 0.5,
                              end_pos[1] - arrow_size * dy - arrow_size * dx * 0.5)
                        p2 = (end_pos[0] - arrow_size * dx - arrow_size * dy * 0.5,
                              end_pos[1] - arrow_size * dy + arrow_size * dx * 0.5)
                        
                        draw.polygon([end_pos, p1, p2], fill=self.pen_color)
                
                elif ann_type == "text":
                    text = data.get("text", "")
                    draw.text(pos, text, fill=self.pen_color, font=font)
                
                elif ann_type == "rectangle":
                    size = data.get("size", (100, 50))
                    draw.rectangle([
                        pos[0], pos[1],
                        pos[0] + size[0], pos[1] + size[1]
                    ], outline=self.pen_color, width=self.pen_width)
            
            self.annotation_overlay = overlay
            return overlay
            
        except Exception as e:
            self.logger.error(f"Error creating annotation overlay: {e}")
            return Image.new("RGBA", screen_size, (0, 0, 0, 0))


class AdaptiveQuality:
    """Manages adaptive quality based on network conditions"""
    
    def __init__(self, screen_capture: ScreenCapture):
        """Initialize adaptive quality manager"""
        self.screen_capture = screen_capture
        self.logger = logging.getLogger(__name__)
        
        # Quality metrics
        self.network_quality = "good"  # good, fair, poor
        self.frame_loss_rate = 0.0
        self.latency = 0.0
        
        # Quality adjustment
        self.quality_levels = ["low", "medium", "high", "ultra"]
        self.current_level_index = 1  # Start with medium
        
        # Monitoring
        self.adjustment_interval = 10  # seconds
        self.last_adjustment = 0
        
    def update_network_metrics(self, latency: float, packet_loss: float):
        """Update network quality metrics"""
        self.latency = latency
        self.frame_loss_rate = packet_loss
        
        # Determine network quality
        if latency < 50 and packet_loss < 0.01:
            self.network_quality = "good"
        elif latency < 150 and packet_loss < 0.05:
            self.network_quality = "fair"
        else:
            self.network_quality = "poor"
        
        # Check if adjustment is needed
        current_time = time.time()
        if current_time - self.last_adjustment > self.adjustment_interval:
            self._adjust_quality()
            self.last_adjustment = current_time
    
    def _adjust_quality(self):
        """Adjust quality based on network conditions"""
        try:
            old_level = self.quality_levels[self.current_level_index]
            
            if self.network_quality == "poor" and self.current_level_index > 0:
                # Decrease quality
                self.current_level_index -= 1
            elif self.network_quality == "good" and self.current_level_index < len(self.quality_levels) - 1:
                # Increase quality
                self.current_level_index += 1
            
            new_level = self.quality_levels[self.current_level_index]
            
            if old_level != new_level:
                self.screen_capture.set_quality(new_level)
                self.logger.info(f"Quality adjusted from {old_level} to {new_level} "
                               f"(network: {self.network_quality})")
                
        except Exception as e:
            self.logger.error(f"Error adjusting quality: {e}")
    
    def force_quality(self, quality: str):
        """Force specific quality level"""
        if quality in self.quality_levels:
            self.current_level_index = self.quality_levels.index(quality)
            self.screen_capture.set_quality(quality)
            self.logger.info(f"Quality forced to {quality}")
    
    def get_current_quality(self) -> str:
        """Get current quality level"""
        return self.quality_levels[self.current_level_index]


# Utility functions
def optimize_for_lan():
    """Optimize screen capture settings for LAN"""
    return {
        "fps": 20,
        "scale_factor": 0.8,
        "quality": "high"
    }


def optimize_for_internet():
    """Optimize screen capture settings for internet"""
    return {
        "fps": 10,
        "scale_factor": 0.5,
        "quality": "low"
    }


def get_optimal_resolution(monitor_resolution: Tuple[int, int], 
                          connection_type: str = "lan") -> Tuple[int, int]:
    """Get optimal resolution based on connection type"""
    width, height = monitor_resolution
    
    if connection_type == "lan":
        # Higher resolution for LAN
        scale = 0.75 if width > 1920 else 1.0
    else:
        # Lower resolution for internet
        scale = 0.5 if width > 1920 else 0.6
    
    return (int(width * scale), int(height * scale))