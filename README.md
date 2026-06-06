# Face Recognition Attendance System

A premium Apple-inspired desktop application for face recognition based attendance tracking, built with Python, OpenCV, and CustomTkinter.

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

```
face-attendance-glass/
├── app.py                  # Main application entry point
├── database.py             # SQLite database manager
├── face_manager.py         # Face recognition logic
├── attendance_manager.py   # Attendance tracking
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── known_faces/            # Stored face images
├── attendance_data/        # CSV attendance files
├── ui_components/          # UI component modules
│   ├── __init__.py
│   ├── theme.py            # Theme manager (dark/light)
│   ├── sidebar.py          # Left navigation sidebar
│   ├── pages.py            # All application pages
│   └── widgets.py          # Reusable glass widgets
└── assets/                 # Icons and images
    ├── ui/
    └── icons/
```

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3 | Core language |
| OpenCV | Camera capture & image processing |
| face_recognition | Face detection & encoding |
| CustomTkinter | Modern UI framework |
| Pillow | Image handling |
| NumPy | Array operations |
| SQLite | Database storage |
| CSV | Attendance export |
| Matplotlib | Charts and graphs |

## Usage

1. Add face images to `known_faces/` folder (filename = person name, e.g. `Mishal.jpg`)
2. Launch the app — faces are loaded automatically
3. Click **Start Camera** on the Home page
4. The system detects and recognizes faces in real-time
5. Attendance is marked automatically when a known face is detected
6. Use **Register Person** when an unknown face appears
7. View records, generate reports, and export data from the sidebar pages

## Face Image Tips

- Use clear, well-lit photos
- One face per image
- Front-facing photos work best
- Supported formats: JPG, JPEG, PNG

## License

MIT License
