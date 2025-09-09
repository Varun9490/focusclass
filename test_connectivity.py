#!/usr/bin/env python3
"""
Network connectivity test utility for FocusClass
Helps diagnose connection issues between student and teacher
"""

import socket
import requests
import time
import sys
from pathlib import Path

def test_tcp_connection(host, port, timeout=10):
    """Test TCP connection to host:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"TCP test error: {e}")
        return False

def test_http_connection(host, port, timeout=10):
    """Test HTTP connection"""
    try:
        url = f"http://{host}:{port}/api/session/test"
        response = requests.get(url, timeout=timeout)
        return response.status_code in [200, 404]  # 404 is OK, means server responded
    except Exception as e:
        print(f"HTTP test error: {e}")
        return False

def ping_host(host):
    """Ping host to test basic connectivity"""
    import subprocess
    try:
        # Use ping command
        result = subprocess.run(
            ['ping', '-n', '1', host] if sys.platform == 'win32' else ['ping', '-c', '1', host],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Ping error: {e}")
        return False

def main():
    """Main connectivity test"""
    if len(sys.argv) != 2:
        print("Usage: python test_connectivity.py <teacher_ip>")
        print("Example: python test_connectivity.py 172.168.1.197")
        sys.exit(1)
    
    teacher_ip = sys.argv[1]
    
    print(f"🔧 FocusClass Network Connectivity Test")
    print(f"Testing connection to teacher at: {teacher_ip}")
    print("=" * 50)
    
    # Test 1: Basic ping
    print("1. Testing basic connectivity (ping)...")
    if ping_host(teacher_ip):
        print("   ✅ PASS: Host is reachable")
    else:
        print("   ❌ FAIL: Host is not reachable")
        print("   💡 Check if the IP address is correct and the teacher's computer is on")
    
    # Test 2: WebSocket port (8765)
    print("\\n2. Testing WebSocket port (8765)...")
    if test_tcp_connection(teacher_ip, 8765):
        print("   ✅ PASS: WebSocket port is open")
    else:
        print("   ❌ FAIL: WebSocket port is not accessible")
        print("   💡 Check if teacher has started a session and firewall is not blocking port 8765")
    
    # Test 3: HTTP port (8080)
    print("\\n3. Testing HTTP port (8080)...")
    if test_tcp_connection(teacher_ip, 8080):
        print("   ✅ PASS: HTTP port is open")
    else:
        print("   ❌ FAIL: HTTP port is not accessible")
        print("   💡 Check if teacher has started a session and firewall is not blocking port 8080")
    
    # Test 4: HTTP API response
    print("\\n4. Testing HTTP API response...")
    if test_http_connection(teacher_ip, 8080):
        print("   ✅ PASS: HTTP server is responding")
    else:
        print("   ❌ FAIL: HTTP server is not responding")
        print("   💡 Teacher session may not be started or there may be a firewall issue")
    
    print("\\n" + "=" * 50)
    print("🔍 Troubleshooting Tips:")
    print("1. Make sure teacher has started a session")
    print("2. Check Windows Firewall settings on teacher's computer")
    print("3. Verify both computers are on the same network")
    print("4. Try temporarily disabling antivirus/firewall for testing")
    print("5. Check if any VPN is interfering with local network access")

if __name__ == "__main__":
    main()