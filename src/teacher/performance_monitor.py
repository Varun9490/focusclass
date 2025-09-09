"""
Performance Monitoring for FocusClass
"""

import psutil
import time

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.last_net_io = psutil.net_io_counters()

    def get_stats(self):
        """Get current performance statistics"""
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_info = psutil.virtual_memory()
        
        # Network usage
        current_net_io = psutil.net_io_counters()
        elapsed_time = time.time() - self.start_time
        
        bytes_sent = current_net_io.bytes_sent - self.last_net_io.bytes_sent
        bytes_recv = current_net_io.bytes_recv - self.last_net_io.bytes_recv
        
        send_speed = bytes_sent / elapsed_time if elapsed_time > 0 else 0
        recv_speed = bytes_recv / elapsed_time if elapsed_time > 0 else 0
        
        self.start_time = time.time()
        self.last_net_io = current_net_io
        
        return {
            "cpu_usage": cpu_usage,
            "memory_percent": memory_info.percent,
            "memory_used": memory_info.used,
            "memory_total": memory_info.total,
            "net_send_speed": send_speed,
            "net_recv_speed": recv_speed,
        }
