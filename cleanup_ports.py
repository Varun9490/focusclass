#!/usr/bin/env python3
"""
Cleanup ports used by FocusClass
"""

import subprocess
import sys

def cleanup_ports():
    """Clean up ports 8765 and 8080"""
    ports = [8765, 8080]
    
    for port in ports:
        try:
            print(f"Checking port {port}...")
            
            # Find processes using the port
            result = subprocess.run([
                'netstat', '-ano'
            ], capture_output=True, text=True, shell=True)
            
            lines = result.stdout.split('\n')
            for line in lines:
                if f':{port} ' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"Found process {pid} using port {port}")
                        
                        # Kill the process
                        try:
                            subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
                            print(f"Killed process {pid}")
                        except subprocess.CalledProcessError as e:
                            print(f"Failed to kill process {pid}: {e}")
                            
        except Exception as e:
            print(f"Error checking port {port}: {e}")
    
    print("Port cleanup completed")

if __name__ == "__main__":
    cleanup_ports()