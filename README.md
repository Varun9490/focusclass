# FocusClass - Teacher-Student Monitoring & Screen Sharing App

A comprehensive Python-based application for classroom management, screen sharing, and student monitoring over LAN networks.

## 🎯 Features

### Teacher Application (Teacher.exe)
- **Session Management**: Start/stop sessions with unique codes and passwords
- **Screen Broadcasting**: Share teacher's screen with all students in real-time
- **Focus Mode**: Enforce restrictions on student devices to maintain attention
- **Student Monitoring**: View individual student screens on demand
- **Violation Tracking**: Monitor and log student violations of focus mode
- **Database Logging**: SQLite database for attendance, violations, and session data
- **QR Code Generation**: Easy connection for students via QR codes

### Student Application (Student.exe)
- **Easy Connection**: Connect via IP + password or QR code scanning
- **Teacher's Screen View**: Receive teacher's screen broadcast
- **Focus Mode Compliance**: Automatic restrictions when enabled
- **Screen Sharing**: Share screen with teacher when requested
- **Auto-Discovery**: Find teachers on local network automatically

## 🚀 Quick Start

### For Teachers

1. **Run Teacher.exe**
2. **Start Session**: Click "Start Session" button
3. **Share Details**: Give students the session code and password (or let them scan QR code)
4. **Begin Teaching**: Start screen sharing and optionally enable focus mode

### For Students

1. **Run Student.exe**
2. **Connect**: Enter teacher's details or scan QR code
3. **Join Session**: You'll see teacher's screen when sharing begins
4. **Follow Rules**: Comply with focus mode restrictions if enabled

## 🛠️ Installation

### Prerequisites
- Windows 10 or later
- Python 3.8+ (for development)
- Administrator privileges (recommended for full focus mode)

### Quick Setup (End Users)
1. Download the release package
2. Extract all files to a folder
3. Run `install.bat` for setup
4. Use `Teacher.exe` and `Student.exe`

### Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd FocusClass

# Install dependencies
pip install -r requirements.txt

# Run teacher application
python src/teacher/teacher_app.py

# Run student application (in another terminal)
python src/student/student_app.py
```

### Building Executables
```bash
# Install PyInstaller
pip install pyinstaller

# Run build script
python build.py

# Or use the batch file on Windows
build.bat
```

## 📖 Detailed Usage

### Teacher Application

#### Starting a Session
1. Launch Teacher.exe
2. Click "Start Session"
3. Session code and password are automatically generated
4. QR code appears for easy student connection
5. Share the IP, session code, and password with students

#### Screen Sharing
1. Click "Start Screen Sharing" after session begins
2. Your screen will be broadcast to all connected students
3. Quality automatically adjusts based on network conditions
4. Click "Stop Screen Sharing" to end broadcast

#### Focus Mode
1. Check "Enable Focus Mode" to restrict student devices
2. Students cannot switch applications or access system functions
3. Violations are logged and displayed in real-time
4. Use responsibly and ensure students understand the restrictions

#### Student Monitoring
1. Connected students appear in the student list
2. Click "View Screen" to request student's screen
3. Student must approve the request (unless auto-approve enabled)
4. Click "Kick" to remove a disruptive student

#### Session Management
- View real-time student count and status
- Monitor violations and attendance
- Export session data for records
- End session to disconnect all students

### Student Application

#### Connecting to Teacher
1. Launch Student.exe
2. Choose connection method:
   - **Manual**: Enter IP, session code, password, and your name
   - **QR Code**: Scan or paste QR code from teacher's screen
   - **Discovery**: Auto-find teachers on network (if available)
3. Click OK to connect

#### Viewing Teacher's Screen
- Teacher's screen appears in the main window
- Use fullscreen mode for better viewing
- Connection status shown in bottom right

#### Focus Mode
- When enabled, application switching is restricted
- Notifications are blocked
- Violations are logged and reported to teacher
- Stay in the application to avoid penalties

#### Screen Sharing Requests
- Teacher may request to view your screen
- Approve or deny the request when prompted
- Enable "Auto-approve" for automatic acceptance
- Sharing shows your entire screen to the teacher

## ⚙️ Configuration

### Network Settings
- **WebSocket Port**: Default 8765 (for real-time communication)
- **HTTP Port**: Default 8080 (for REST API and file serving)
- **Max Students**: Default 200 per session

### Screen Capture Settings
- **Quality Presets**: Low, Medium, High, Ultra
- **Frame Rate**: 5-60 FPS (default 15)
- **Scale Factor**: 0.1-2.0 (default 0.75)
- **Adaptive Quality**: Automatically adjusts based on network

### Focus Mode Settings
- **Admin Mode**: Full restrictions (requires administrator rights)
- **Lightweight Mode**: Basic restrictions (works without admin)
- **Violation Tracking**: Logs Alt+Tab, Win key, Ctrl+Esc usage

## 🔧 Network Setup

### LAN (Recommended)
- Connect all devices to the same Wi-Fi network
- Teacher's IP is displayed in the application
- Students connect using teacher's IP address
- No additional configuration required

### Internet Connection
For connections over the internet:
1. Configure router port forwarding:
   - Forward port 8765 (WebSocket)
   - Forward port 8080 (HTTP)
2. Use teacher's public IP address
3. Ensure firewall allows the applications

### Firewall Configuration
Add firewall exceptions for:
- Teacher.exe (incoming connections)
- Student.exe (outgoing connections)
- Ports 8765 and 8080

## 🔍 Troubleshooting

### Connection Issues

**Students can't connect:**
- Verify teacher's IP address
- Check firewall settings
- Ensure all devices on same network
- Try restarting both applications

**Poor video quality:**
- Check network bandwidth
- Lower video quality settings
- Use wired connection if possible
- Close unnecessary applications

### Focus Mode Issues

**Restrictions not working:**
- Run Student.exe as administrator
- Check antivirus interference
- Verify Windows version compatibility
- Try lightweight mode if admin unavailable

**False violation reports:**
- Adjust violation sensitivity
- Check for background processes
- Update Windows and drivers

### Performance Issues

**High CPU usage:**
- Lower frame rate and resolution
- Close background applications
- Update graphics drivers

**Memory issues:**
- Restart applications periodically
- Limit number of concurrent students
- Monitor system resources

## 🏗️ Architecture

### Components
```
FocusClass/
├── src/
│   ├── teacher/           # Teacher application
│   ├── student/           # Student application
│   └── common/            # Shared modules
│       ├── database_manager.py    # SQLite operations
│       ├── network_manager.py     # WebRTC/WebSocket
│       ├── screen_capture.py      # Screen recording
│       ├── focus_manager.py       # Windows restrictions
│       ├── utils.py              # Utility functions
│       └── config.py             # Configuration
├── assets/                # Icons and resources
├── logs/                  # Application logs
├── exports/               # Session data exports
└── dist/                  # Built executables
```

### Technology Stack
- **GUI**: PyQt5 for cross-platform interface
- **Networking**: WebRTC (aiortc) for video, WebSocket for control
- **Database**: SQLite for session and violation logging
- **Screen Capture**: MSS and OpenCV for efficient capture
- **Security**: Built-in password protection and session codes

### Communication Flow
```
Teacher ←→ WebSocket Control ←→ Student
    ↓           ↓                ↓
Database    WebRTC Video      Focus Manager
    ↓           ↓                ↓
Logs        Screen Stream    Restrictions
```

## 🔒 Security Features

### Session Security
- Random session codes and passwords
- WebRTC encryption (DTLS-SRTP)
- Session timeout and cleanup
- Manual student approval

### Privacy Protection
- Screen sharing requires explicit consent
- Local data storage only
- No cloud dependencies
- Admin-controlled access

### Focus Mode Safety
- Tamper detection and logging
- Graceful degradation without admin rights
- Violation tracking without punishment
- Teacher override capabilities

## 📊 Logging and Reports

### Database Tables
- **Sessions**: Session details and timing
- **Students**: Student attendance and info
- **Violations**: Focus mode violations
- **Activities**: General session activities
- **Screen Requests**: Screen sharing history

### Export Formats
- CSV for spreadsheet analysis
- JSON for programmatic access
- PDF reports (basic text format)

### Log Files
- `logs/teacher.log`: Teacher application logs
- `logs/student.log`: Student application logs
- `logs/focusclass.db`: SQLite database

## 🚧 Limitations & Known Issues

### Current Limitations
- Windows-only focus mode restrictions
- LAN-optimized (internet requires setup)
- Maximum 200 students per session
- Single teacher per session

### Known Issues
- Some antivirus software may flag focus mode
- Screen sharing may have delay on slow networks
- Focus mode bypass possible with advanced users
- WebRTC may not work through some firewalls

### Future Improvements
- Cross-platform focus mode
- Cloud-based sessions
- Mobile app support
- Advanced analytics
- Whiteboard features

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m pytest tests/`
4. Follow PEP 8 style guidelines

### Code Structure
- Use async/await for network operations
- Follow Qt best practices for GUI
- Add logging for debugging
- Include type hints
- Write docstrings

### Reporting Issues
- Use GitHub issues
- Include logs and system info
- Describe reproduction steps
- Mention operating system and Python version

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

### Getting Help
- Check this README for common issues
- Review log files for error details
- Search existing GitHub issues
- Contact development team

### System Requirements
- **Minimum**: Windows 10, 4GB RAM, 1GB disk space
- **Recommended**: Windows 11, 8GB RAM, 2GB disk space, dedicated graphics
- **Network**: 100 Mbps LAN for best performance

## 🎓 Educational Use

### Classroom Guidelines
- Explain focus mode to students before use
- Use screen monitoring responsibly
- Respect student privacy
- Provide breaks from restrictions
- Have backup lesson plans if technology fails

### Best Practices
- Test setup before class
- Train students on connection process
- Monitor network performance
- Keep session logs for record-keeping
- Regular software updates

---

**FocusClass v1.0.0** - Empowering focused learning through technology