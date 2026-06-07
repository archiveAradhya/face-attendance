# Face Recognition Attendance System

## 🎯 Project Overview

A premium Apple-inspired desktop application for face recognition based attendance tracking. Built with Python, OpenCV, DeepFace, and CustomTkinter featuring glassmorphism design, real-time face detection, automatic attendance marking, and comprehensive database management.

## ✨ Features

### 🎨 Premium UI Design
- **Apple-inspired glassmorphism design** with frosted glass effects
- **Dark/Light theme switching** with smooth transitions
- **Responsive layout** with professional typography
- **Smooth animations** and modern macOS-style spacing

### 📹 Face Recognition System
- **Real-time camera feed** with face detection
- **Automatic face recognition** with confidence scores
- **Unknown face registration** on-the-fly
- **Multiple camera support** with device selection
- **Configurable confidence thresholds**

### 📊 Attendance Management
- **Automatic attendance marking** (once per day per person)
- **Duplicate prevention** to avoid multiple entries
- **SQLite database** for persistent storage
- **CSV export functionality** for data analysis
- **Daily, weekly, monthly views**

### 🗃️ Database Features
- **User management** with CRUD operations
- **Face image storage** with automatic encoding
- **Attendance history tracking**
- **Department-based organization**
- **Search and filtering capabilities**

### 📈 Reports & Analytics
- **Attendance summaries** with statistics
- **Recognition performance** metrics
- **Present/absent ratios** and percentages
- **Trend analysis** with visual charts
- **Department-wise attendance** reports

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3** | Core application language |
| **OpenCV** | Camera capture & image processing |
| **DeepFace** | Face matching and verification |
| **CustomTkinter** | Modern UI framework |
| **Pillow** | Image handling & manipulation |
| **NumPy** | Array operations & numerical computing |
| **SQLite** | Database storage & management |
| **CSV** | Data export functionality |
| **Matplotlib** | Charts & graphs for reports |

## 📁 Project Structure

```
face-attendance-glass/
├── app.py                     # Main application entry point
├── database.py                # SQLite database management
├── face_manager.py            # Face recognition logic
├── attendance_manager.py      # Attendance tracking system
├── requirements.txt           # Python dependencies
├── README.md                  # This documentation
├── test_app.py               # Application test script
├── known_faces/               # Face image storage
├── attendance_data/          # CSV attendance files
├── ui_components/            # UI component modules
│   ├── __init__.py
│   ├── theme.py              # Theme manager (dark/light)
│   ├── sidebar.py            # Navigation sidebar
│   ├── pages.py              # Application pages
│   └── widgets.py            # Glassmorphism widgets
└── assets/                   # Icons and images
    ├── ui/
    └── icons/
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Camera device (for face recognition)
- Face images for registered users

### Installation Steps

#### 1. Clone/Download the Project
```bash
# Navigate to project directory
cd /Users/mishalseries/Desktop/face-attendance-glass
```

#### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Prepare Face Images
```bash
# Create known_faces directory (if not exists)
mkdir -p known_faces

# Add face images with filename = person name
# Example: known_faces/Mishal.jpg
# Example: known_faces/Rahul.jpg
```

#### 5. Run the Application
```bash
python app.py
```

## 🎮 User Guide

### Getting Started

1. **Add Face Images**: Place clear face images in the `known_faces/` folder with filenames as person names (e.g., `John_Doe.jpg`)

2. **Launch Application**: Run `python app.py` to start the application

3. **Navigate**: Use the left sidebar to access different sections:
   - **Home**: Live camera feed and real-time statistics
   - **Live Attendance**: Real-time attendance monitoring
   - **Attendance Records**: View historical attendance data
   - **Face Database**: Manage registered users and faces
   - **Reports**: Generate attendance reports and analytics
   - **Settings**: Configure application preferences

### Face Registration

When an unknown face is detected:

1. **Click "Register Person"** on the home page
2. **Fill in user details**: Name, Employee ID, Department
3. **System captures face** automatically
4. **User becomes recognized** immediately after registration
5. **Attendance marked** automatically for the day

### Navigation Features

- **Theme Toggle**: Click moon/sun icon to switch between dark/light modes
- **Auto-refresh**: Data updates every 30 seconds automatically
- **Search**: Use search functionality in Face Database
- **Export**: Export attendance data to CSV format

## 📊 Face Image Guidelines

### Requirements
- **Format**: JPG, JPEG, PNG
- **Size**: One face per image
- **Quality**: Clear, well-lit photos work best
- **Orientation**: Front-facing faces recommended
- **Background**: Simple, plain backgrounds preferred

### File Naming
- Use person's full name as filename
- Example: `John_Doe.jpg`, `Jane_Smith.jpg`
- No special characters or spaces (use underscores)
- Case-sensitive (keep consistent casing)

## 🔧 Configuration

### Camera Settings
- **Device Selection**: Choose from available cameras in Settings
- **Face Detection Confidence**: Adjust sensitivity (0.1-1.0)
- **Recognition Confidence**: Adjust matching threshold (0.1-1.0)

### Database Settings
- **Auto Backup**: Enable automatic database backups
- **Data Retention**: Configure how long to keep attendance data
- **Storage Location**: SQLite database in project root

### Application Settings
- **Notifications**: Enable/disable system notifications
- **Auto Start**: Automatically start camera on launch
- **UI Theme**: Default theme preference

## 🧪 Testing

### Run Test Script
```bash
python test_app.py
```

The test script will verify:
- ✅ All imports working
- ✅ Database functionality
- ✅ Face recognition system
- ✅ Attendance management
- ✅ UI components

### Manual Testing
1. **Camera Test**: Ensure camera is working and accessible
2. **Face Recognition**: Test with known face images
3. **Attendance Marking**: Verify attendance is marked correctly
4. **Database Operations**: Test user management features
5. **UI Responsiveness**: Check theme switching and navigation

## 🚨 Troubleshooting

### Common Issues

**Camera Not Detected**
```bash
# Check available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

**Face Recognition Not Working**
- Ensure face images are properly lit
- Check face images are in correct format
- Verify face detection confidence settings
- Ensure faces are clearly visible in images

**Database Errors**
- Check file permissions for database
- Ensure SQLite is properly installed
- Verify database file isn't corrupted

**UI Issues**
- Ensure CustomTkinter is properly installed
- Check Python version compatibility
- Verify all dependencies are installed

## 🔒 Data Management

### Backup Database
```bash
# Copy database file for backup
cp attendance_system.db backup_attendance_system.db
```

### Export Attendance Data
```bash
# Use Reports page to export CSV
# Or use attendance_manager.export_attendance_csv(filename)
```

### Clean Up Old Data
```python
# Remove attendance records older than 365 days
attendance_manager.cleanup_old_attendance_files(365)
```

## 🎨 Customization

### Theme Colors
Modify colors in `ui_components/theme.py`:
- Dark mode: `DARK_COLORS` dictionary
- Light mode: `LIGHT_COLORS` dictionary

### UI Styling
Adjust widgets in `ui_components/widgets.py`:
- Corner radius values
- Border colors and widths
- Font sizes and styles
- Spacing and padding

### Face Recognition Settings
Tune parameters in `face_manager.py`:
- `face_detection_confidence`: Detection sensitivity
- `recognition_confidence`: Matching threshold
- Camera resolution and frame rate

## 📈 Performance Optimization

### Tips for Better Performance
1. **Use high-quality face images** for better recognition
2. **Optimize lighting conditions** in camera area
3. **Regular database maintenance** to prevent slowdowns
4. **Close unnecessary applications** to free system resources
5. **Update dependencies regularly** for performance improvements

### Memory Management
- Clear unknown faces periodically
- Optimize image processing parameters
- Use appropriate camera resolution
- Implement proper cleanup of resources

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add appropriate comments
- Maintain consistent coding style

## 📄 License

MIT License - Feel free to use this project for personal or commercial purposes.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test script output
3. Ensure all dependencies are installed
4. Verify system requirements are met

## 🎉 Acknowledgments

- **DeepFace** for face matching and verification
- **CustomTkinter** for modern UI components
- **OpenCV** for computer vision capabilities
- **Apple design principles** for UI inspiration

---

**Note**: This is a production-ready application with comprehensive features for face recognition based attendance tracking. The system is designed to be robust, user-friendly, and aesthetically pleasing with premium glassmorphism design elements.
