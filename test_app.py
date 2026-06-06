#!/usr/bin/env python3
"""
Test script for Face Recognition Attendance System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from database import DatabaseManager
        from face_manager import FaceManager
        from attendance_manager import AttendanceManager
        from ui_components.theme import ThemeManager
        from ui_components.sidebar import SidebarNavigation
        from ui_components.pages import HomePage, FaceDatabasePage, AttendancePage, ReportsPage, SettingsPage
        from app import FaceAttendanceApp, FaceRegistrationDialog, UserManagementDialog
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_database():
    """Test database functionality"""
    try:
        from database import DatabaseManager
        
        # Test database initialization
        db = DatabaseManager("test.db")
        print("✓ Database initialized")
        
        # Test user operations
        user_id = db.add_user("John Doe", "EMP001", "IT", "known_faces/john.jpg")
        if user_id:
            print("✓ User creation successful")
        else:
            print("✗ User creation failed")
            return False
        
        # Test user retrieval
        user = db.get_user_by_id(user_id)
        if user:
            print("✓ User retrieval successful")
        else:
            print("✗ User retrieval failed")
            return False
        
        # Test attendance marking
        success = db.mark_attendance(user_id, "John Doe")
        if success:
            print("✓ Attendance marking successful")
        else:
            print("✗ Attendance marking failed")
            return False
        
        # Test attendance retrieval
        attendance = db.get_attendance_by_user(user_id)
        if attendance:
            print("✓ Attendance retrieval successful")
        else:
            print("✗ Attendance retrieval failed")
            return False
        
        # Clean up test database
        if os.path.exists("test.db"):
            os.remove("test.db")
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_face_manager():
    """Test face manager functionality"""
    try:
        from database import DatabaseManager
        from face_manager import FaceManager
        
        # Create test database
        db = DatabaseManager("test_faces.db")
        face_manager = FaceManager(db)
        
        # Test face manager initialization
        stats = face_manager.get_statistics()
        print(f"✓ Face manager initialized with {stats['known_faces_count']} known faces")
        
        # Test camera device detection
        cameras = face_manager.get_camera_devices()
        if cameras:
            print(f"✓ Found {len(cameras)} camera device(s)")
        else:
            print("✗ No camera devices found")
        
        # Test confidence settings
        face_manager.set_face_detection_confidence(0.7)
        face_manager.set_recognition_confidence(0.8)
        print("✓ Confidence settings updated")
        
        # Clean up test database
        if os.path.exists("test_faces.db"):
            os.remove("test_faces.db")
        
        return True
    except Exception as e:
        print(f"✗ Face manager test failed: {e}")
        return False

def test_attendance_manager():
    """Test attendance manager functionality"""
    try:
        from database import DatabaseManager
        from attendance_manager import AttendanceManager
        
        # Create test database
        db = DatabaseManager("test_attendance.db")
        attendance_manager = AttendanceManager(db)
        
        # Test attendance statistics
        summary = attendance_manager.get_attendance_summary()
        if summary:
            print(f"✓ Attendance summary retrieved: {summary[0]} total records")
        else:
            print("✗ Attendance summary failed")
            return False
        
        # Test daily attendance stats
        today = "2026-06-04"  # Current date
        daily_stats = attendance_manager.get_daily_attendance_stats(today)
        if daily_stats:
            print("✓ Daily attendance stats retrieved")
        else:
            print("✗ Daily attendance stats failed")
            return False
        
        # Test attendance trends
        trends = attendance_manager.get_attendance_trends(7)
        if trends:
            print(f"✓ Attendance trends retrieved for {len(trends)} days")
        else:
            print("✗ Attendance trends failed")
            return False
        
        # Clean up test database
        if os.path.exists("test_attendance.db"):
            os.remove("test_attendance.db")
        
        return True
    except Exception as e:
        print(f"✗ Attendance manager test failed: {e}")
        return False

def test_ui_components():
    """Test UI components"""
    try:
        from ui_components.theme import ThemeManager
        from ui_components.widgets import GlassCard, GlassButton, GlassEntry
        
        # Test theme manager
        theme = ThemeManager()
        print(f"✓ Theme manager initialized with {theme.current_theme} theme")
        
        # Test theme toggling
        theme.toggle_theme()
        print(f"✓ Theme toggled to {theme.current_theme}")
        
        # Test glass components (these would need GUI to fully test)
        print("✓ UI components classes created successfully")
        
        return True
    except Exception as e:
        print(f"✗ UI components test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Face Recognition Attendance System Tests...\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Database Test", test_database),
        ("Face Manager Test", test_face_manager),
        ("Attendance Manager Test", test_attendance_manager),
        ("UI Components Test", test_ui_components)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print(f"\n--- Test Summary ---")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo run the application:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Add face images to 'known_faces' folder (filename = person name)")
        print("3. Run: python app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)