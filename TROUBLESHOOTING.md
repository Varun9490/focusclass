# FocusClass Connection Troubleshooting Guide

## 🔧 Student Cannot Connect to Teacher

### Quick Diagnosis Steps:

1. **Test Network Connectivity**
   ```bash
   python test_connectivity.py <teacher_ip>
   ```
   Example: `python test_connectivity.py 172.168.1.197`

2. **Check Teacher Session Status**
   - Ensure teacher has clicked "Start Session"
   - Session details should be visible in teacher app
   - Look for logs: "Teacher server started" and "Session started"

3. **Verify Network Settings**
   - Both computers must be on the same network
   - Check IP address is correct (teacher shows IP in session details)
   - No VPN interference

### Common Issues and Solutions:

#### ❌ "The semaphore timeout period has expired"
**Cause**: Network timeout - teacher not reachable
**Solutions**:
- Check teacher has started session
- Verify IP address is correct
- Test with `ping <teacher_ip>`
- Check Windows Firewall settings

#### ❌ "Cannot connect to host X.X.X.X:8080"
**Cause**: HTTP port blocked or teacher not running
**Solutions**:
- Teacher must click "Start Session" first
- Windows Firewall may be blocking ports 8080 and 8765
- Try temporarily disabling firewall for testing

#### ❌ "Connection timeout"
**Cause**: Network unreachable or firewall blocking
**Solutions**:
- Ensure both on same WiFi/network
- Check router settings if using different subnets
- Antivirus may be blocking connections

### Windows Firewall Configuration:

1. **Allow FocusClass through Windows Firewall**:
   - Windows Settings → Privacy & Security → Windows Security
   - Firewall & network protection → Allow an app through firewall
   - Add Python.exe or the specific FocusClass executable

2. **Open Required Ports**:
   - Port 8765 (WebSocket)
   - Port 8080 (HTTP API)

3. **Temporary Testing**:
   - Disable Windows Firewall temporarily
   - If connection works, add firewall exceptions

### Network Troubleshooting Commands:

```bash
# Test basic connectivity
ping <teacher_ip>

# Test specific ports
telnet <teacher_ip> 8080
telnet <teacher_ip> 8765

# Check local network configuration
ipconfig /all      # Windows
ifconfig           # Linux/Mac
```

### Teacher-Side Checklist:

- [ ] Session started successfully
- [ ] No errors in teacher logs
- [ ] Correct IP address displayed
- [ ] Ports 8080 and 8765 not blocked
- [ ] Windows Firewall allows connections

### Student-Side Checklist:

- [ ] Correct teacher IP address
- [ ] Correct session code and password
- [ ] On same network as teacher
- [ ] No VPN interfering
- [ ] Windows Firewall allows outbound connections

### Advanced Debugging:

1. **Check Teacher Logs**:
   Look for: "Teacher server started" and HTTP/WebSocket startup messages

2. **Check Student Logs**:
   Look for detailed connection attempt logs

3. **Network Analysis**:
   - Use `netstat -an` on teacher computer to verify ports are listening
   - Use network scanner tools to check port accessibility

### Quick Fix Checklist:

1. ✅ Teacher clicked "Start Session"
2. ✅ Both on same network
3. ✅ Correct IP address
4. ✅ Windows Firewall exceptions added
5. ✅ No antivirus blocking
6. ✅ No VPN interference

If all else fails, try connecting both computers via Ethernet cable for testing.