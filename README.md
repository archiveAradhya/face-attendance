# Face Recognition Attendance System

A premium Apple-inspired desktop application for face recognition based attendance tracking, built with Python, OpenCV, DeepFace, and CustomTkinter.

## Features

- **Real-time Face Recognition** – Live webcam feed with instant face detection and identification
- **Automatic Attendance** – Marks attendance with duplicate prevention (once per day per person)
- **Unknown Face Registration** – On-the-fly registration of unknown persons
- **Face Database Management** – Add, edit, delete, and update registered faces
- **Attendance Records** – Daily, weekly, and monthly views with search and filter
- **Reports & Analytics** – Attendance summaries, recognition statistics, and visual charts
- **CSV Export** – Export attendance records to CSV
- **SQLite Storage** – Persistent database for users and attendance
- **Glassmorphism UI** – Apple-inspired frosted glass design
- **Dark / Light Mode** – Beautiful theme switching

## Installation

### macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Project Structure

```text
face-attendance/
├── app.py                  # Main application entry point
├── database.py             # SQLite database manager
├── face_manager.py         # Face detection and recognition logic
├── attendance_manager.py   # Attendance tracking and data handling
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── PROJECT_OVERVIEW.md     # Project overview and feature summary
├── test_app.py             # Basic app tests/checks
│
├── ui_components/          # UI component modules
│   ├── __init__.py
│   ├── theme.py            # Dark/light theme manager
│   ├── sidebar.py          # Left navigation sidebar
│   ├── pages.py            # Application pages
│   └── widgets.py          # Reusable UI widgets
│
├── assets/                 # Icons, images, and UI assets
│
├── known_faces/            # Local registered face images
│                           # Ignored from GitHub for privacy
│
├── attendance_data/        # Local attendance CSV files
│                           # Ignored from GitHub
│
└── attendance_system.db    # Local SQLite database
                            # Ignored from GitHub

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3 | Core language |
| OpenCV | Camera capture & image processing |
| DeepFace | Face matching and verification |
| CustomTkinter | Modern UI framework |
| Pillow | Image handling |
| NumPy | Array operations |
| SQLite | Database storage |
| CSV | Attendance export |
| Matplotlib | Charts and graphs |

## Usage

1. Launch the app
2. Click **Start Camera** on the Home page
3. The system detects and recognizes faces in real-time
4. Attendance is marked automatically when a known face is detected
5. Use **Register Face** near the camera controls to capture and save a new profile
6. View records, generate reports, and export data from the sidebar pages

## Face Image Tips

- Use clear, well-lit photos
- One face per image
- Front-facing photos work best
- Supported formats: JPG, JPEG, PNG

## License

MIT License
