# ESTOP Function Record System (EFRS)

A mobile-friendly Flask web application for recording and tracking safety device testing in industrial environments.

## Features

### Core Functionality
- **Machine Selection**: Dropdown interface to select industrial machines
- **Safety Device Testing**: Test emergency stop buttons, safety curtains, interlocks, etc.
- **PASS/FAIL Recording**: Large, mobile-friendly buttons for test results
- **User Authentication**: Integration with RACE user system
- **Test History**: Comprehensive search and filtering of test records
- **Age-Based Color Coding**: Visual indicators for overdue safety tests

### Mobile-First Design
- **Responsive Layout**: Optimized for phones and tablets
- **Touch-Friendly Controls**: Large buttons and form elements
- **Auto-Selection**: First safety device automatically selected
- **Real-Time Search**: Instant filtering as you type

### Advanced Features
- **SQL Server Integration**: Connects to EFRS database (192.168.10.69)
- **Age Tracking**: Color gradient from green (0 days) to red (180+ days)
- **Search & Filter**: By machine, user, device name, or test date
- **Audit Trail**: Complete record of who tested what and when
- **Debug Interface**: System monitoring and endpoint testing

## Quick Start

### Prerequisites
- Python 3.7+
- SQL Server access to 192.168.10.69 (EFRS database)
- Access to /home/eraser/PycharmProjects/RACE/users.json

### Installation
```bash
# Navigate to the project directory
cd /home/eraser/PycharmProjects/ESTOP_System

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

### First Time Setup
The application will automatically:
1. Create database tables if they don't exist
2. Insert sample machines and safety devices
3. Set up authentication using RACE users

### Access the Application
- **Main Application**: http://localhost:5000/
- **Login Page**: http://localhost:5000/login
- **Test History**: http://localhost:5000/history
- **Debug Interface**: http://localhost:5000/debug

## User Guide

### Testing a Safety Device
1. **Login**: Use your RACE system credentials
2. **Select Machine**: Choose from the dropdown list
3. **Choose Device**: First safety device auto-selects
4. **Perform Test**: Press green PASS or red FAIL button
5. **Add Notes**: Optional notes field appears
6. **Confirm**: Review and save the test record

### Viewing Test History
1. Navigate to **View History** from the main menu
2. **Search**: Type device or machine names for instant filtering
3. **Filter**: Use dropdowns for machine or user filters
4. **Sort**: Choose sorting by date, age, machine, or device name
5. **Color Coding**: 
   - Green: 0-30 days (recent)
   - Yellow: 31-90 days (good)
   - Orange: 91-150 days (attention needed)
   - Red: 180+ days (overdue!)

## Authentication

The system uses the existing RACE user database:
- **File**: `/home/eraser/PycharmProjects/RACE/users.json`
- **Users**: ckull, mhiggins, jpetereit, smyers
- **Privileges**: Inherited from RACE system

## Database Schema

### Tables Created Automatically
- **machines**: Machine registry with names and locations
- **safety_devices**: Safety devices linked to machines
- **test_records**: Complete audit trail of all tests
- **user_auth tables**: Session tracking for each user

### Sample Data
The system includes sample machines and devices:
- Machine A, B, C (Production lines)
- CNC Mill (Machine shop)
- Press 1 (Stamping department)
- Various E-stops, light curtains, interlocks

## Mobile Optimization

### Touch Interface
- Large PASS/FAIL buttons (minimum 50px height)
- Generous spacing for finger navigation
- Auto-focus on important fields
- Smooth animations and transitions

### Responsive Design
- Bootstrap 5 responsive grid
- Mobile-first CSS approach
- Scalable font sizes
- Optimized for portrait mode

## Color Legend for Test Age

| Age Range | Color | Status | Action Needed |
|-----------|-------|--------|---------------|
| 0-30 days | Green | Recent | None |
| 31-60 days | Light Yellow | Good | None |
| 61-90 days | Orange | Fair | Monitor |
| 91-120 days | Light Red | Attention | Schedule Soon |
| 121-150 days | Red | Critical | Schedule Now |
| 151-180 days | Dark Red | Critical | Urgent |
| 180+ days | Pulsing Red | Overdue | Immediate Action |

## Development

### Project Structure
```
ESTOP_System/
├── app/
│   ├── __init__.py           # Main Flask application
│   ├── models/
│   │   └── database.py       # SQL Server database model
│   ├── utils/
│   │   └── auth.py          # RACE authentication
│   ├── templates/           # HTML templates
│   └── static/             # CSS, JS, Bootstrap
├── tests/
│   └── test_app.py         # Unit tests
├── logs/                   # Application logs
├── backups/               # Automatic backups
├── requirements.txt       # Python dependencies
├── run.py                # Startup script
└── README.md             # This file
```

### Testing
```bash
# Run unit tests
python tests/test_app.py

# Run with coverage (if installed)
python -m pytest tests/ --cov=app
```

### Debug Mode
```bash
# Start with debug enabled
python run.py --debug
```

## Logging

All actions are logged to:
- **File**: `logs/app.log`
- **Console**: Standard output
- **Format**: Timestamp, level, module, message

## Backup Strategy

Following Warp.dev best practices:
- Backups stored in `backups/` directory
- Timestamp format: `YYYYMMDD_HHMMSS`
- Create backup before major changes:
  ```bash
  tar -czf backups/estop_$(date +%Y%m%d_%H%M%S).tar.gz app/
  ```

## Security Considerations

- **Authentication**: Required for all endpoints
- **Session Management**: Secure Flask sessions
- **SQL Injection**: Parameterized queries only
- **Input Validation**: Server-side validation for all inputs

## Troubleshooting

### Common Issues

**Database Connection Failed**
- Verify SQL Server is running on 192.168.10.69
- Check network connectivity
- Confirm credentials (SA/GreenCandyOneBang)

**Users Not Loading**
- Check RACE/users.json exists and is readable
- Verify JSON format is valid

**Mobile Interface Issues**
- Clear browser cache
- Check viewport meta tag
- Verify Bootstrap CSS loaded

### Log Files
Check `logs/app.log` for detailed error information:
```bash
tail -f logs/app.log
```

## Support

For issues or enhancements:
1. Check the debug page: http://localhost:5000/debug
2. Review logs in `logs/app.log`
3. Run the test suite: `python tests/test_app.py`

---

**ESTOP Function Record System v1.0**  
Built with Flask, Bootstrap 5, and SQL Server  
Mobile-optimized for industrial safety testing