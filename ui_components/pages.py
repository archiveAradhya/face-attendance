import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import time
from datetime import datetime, timedelta
from .theme import ThemeManager
from .widgets import (
    GlassCard, GlassButton, GlassEntry, GlassFrame, GlassLabel, 
    GlassImage, CameraView, StatusBadge, ProgressRing, GlassListbox
)

class HomePage(ctk.CTkFrame):
    def __init__(self, master, face_manager=None, attendance_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.face_manager = face_manager
        self.attendance_manager = attendance_manager
        self.theme_manager = ThemeManager()
        
        self.camera_active = False
        self.camera_thread = None
        
        self.configure(fg_color="transparent")
        self.create_home_page()
    
    def create_home_page(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Top bar
        self.create_top_bar(main_container)
        
        # Camera and statistics section
        stats_frame = ctk.CTkFrame(main_container, fg_color="transparent", corner_radius=0)
        stats_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Left side - Camera
        camera_container = ctk.CTkFrame(stats_frame, fg_color="transparent", corner_radius=0)
        camera_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.create_camera_section(camera_container)
        
        # Right side - Statistics
        stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent", corner_radius=0)
        stats_container.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        self.create_statistics_section(stats_container)
        
        # Bottom section - Today's attendance
        bottom_container = ctk.CTkFrame(main_container, fg_color="transparent", corner_radius=0)
        bottom_container.pack(fill="x", pady=(20, 0))
        
        self.create_today_attendance_section(bottom_container)
    
    def create_top_bar(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top_bar.pack(fill="x", pady=(0, 20))
        
        # Welcome section
        welcome_frame = ctk.CTkFrame(top_bar, fg_color="transparent", corner_radius=0)
        welcome_frame.pack(side="left")
        
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text="Welcome Back Admin",
            font=("SF Pro Display", 18, "semibold"),
            text_color=("white", "black")
        )
        welcome_label.pack(side="left", padx=(0, 20))
        
        # Date and time
        date_label = ctk.CTkLabel(
            welcome_frame,
            text=datetime.now().strftime("%A, %B %d, %Y"),
            font=("SF Pro Text", 12),
            text_color=("gray60", "gray40")
        )
        date_label.pack(side="left", padx=(0, 10))
        
        time_label = ctk.CTkLabel(
            welcome_frame,
            text=datetime.now().strftime("%I:%M %p"),
            font=("SF Pro Text", 14, "semibold"),
            text_color=("white", "black")
        )
        time_label.pack(side="left")
        
        # Status badge
        self.status_badge = StatusBadge(top_bar, "active")
        self.status_badge.pack(side="right", padx=20, pady=5)
    
    def create_camera_section(self, parent):
        camera_card = GlassCard(parent)
        camera_card.pack(fill="both", expand=True)
        camera_card.set_title("Live Camera Feed")
        
        self.camera_view = CameraView(camera_card)
        self.camera_view.pack(fill="both", expand=True)
        
        # Camera controls
        controls_frame = ctk.CTkFrame(camera_card, fg_color="transparent", corner_radius=0)
        controls_frame.pack(fill="x", pady=(10, 0))
        
        self.start_button = GlassButton(
            controls_frame,
            text="Start Camera",
            command=self.toggle_camera,
            width=120
        )
        self.start_button.pack(side="left", padx=5)
        
        self.register_button = GlassButton(
            controls_frame,
            text="Register Person",
            command=self.show_registration_dialog,
            width=140,
            state="disabled"
        )
        self.register_button.pack(side="left", padx=5)
        
        # Face detection info
        self.info_label = ctk.CTkLabel(
            controls_frame,
            text="Faces: 0 | Known: 0 | Unknown: 0",
            font=("SF Pro Text", 10),
            text_color=("gray60", "gray40")
        )
        self.info_label.pack(side="right", padx=5)
    
    def create_statistics_section(self, parent):
        # Present Today
        present_card = GlassCard(parent)
        present_card.pack(fill="both", expand=True, pady=(0, 10))
        present_card.set_title("Present Today")
        
        self.present_count = 0
        self.present_ring = ProgressRing(present_card, size=80)
        self.present_ring.pack(pady=10)
        self.present_ring.set_progress(0)
        
        present_label = ctk.CTkLabel(
            present_card,
            text="0 students",
            font=("SF Pro Text", 12),
            text_color=("gray60", "gray40")
        )
        present_label.pack()
        
        # Recognized Faces
        recognized_card = GlassCard(parent)
        recognized_card.pack(fill="both", expand=True, pady=(0, 10))
        recognized_card.set_title("Recognized Faces")
        
        self.recognized_count = 0
        self.recognized_ring = ProgressRing(recognized_card, size=80)
        self.recognized_ring.pack(pady=10)
        self.recognized_ring.set_progress(0)
        
        recognized_label = ctk.CTkLabel(
            recognized_card,
            text="0 faces",
            font=("SF Pro Text", 12),
            text_color=("gray60", "gray40")
        )
        recognized_label.pack()
        
        # Unknown Faces
        unknown_card = GlassCard(parent)
        unknown_card.pack(fill="both", expand=True)
        unknown_card.set_title("Unknown Faces")
        
        self.unknown_count = 0
        self.unknown_ring = ProgressRing(unknown_card, size=80)
        self.unknown_ring.pack(pady=10)
        self.unknown_ring.set_progress(0)
        
        unknown_label = ctk.CTkLabel(
            unknown_card,
            text="0 faces",
            font=("SF Pro Text", 12),
            text_color=("gray60", "gray40")
        )
        unknown_label.pack()
        
        # Total Registered Users
        total_card = GlassCard(parent)
        total_card.pack(fill="both", expand=True)
        total_card.set_title("Total Registered Users")
        
        self.total_users = 0
        self.total_label = ctk.CTkLabel(
            total_card,
            text="0 users",
            font=("SF Pro Display", 20, "semibold"),
            text_color=("white", "black")
        )
        self.total_label.pack(pady=10)
    
    def create_today_attendance_section(self, parent):
        attendance_card = GlassCard(parent)
        attendance_card.pack(fill="both", expand=True)
        attendance_card.set_title("Today's Attendance")
        
        # Scrollable frame for recent attendance
        self.attendance_scroll = ctk.CTkScrollableFrame(
            attendance_card,
            fg_color="transparent",
            corner_radius=0
        )
        self.attendance_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Placeholder for attendance items
        self.attendance_items = []
        self.update_attendance_display()
    
    def toggle_camera(self):
        if not self.camera_active:
            if self.face_manager:
                self.camera_active = True
                self.start_button.configure(text="Stop Camera")
                self.register_button.configure(state="normal")
                
                # Start camera thread
                self.camera_thread = threading.Thread(target=self.start_camera_capture)
                self.camera_thread.daemon = True
                self.camera_thread.start()
        else:
            self.stop_camera()
    
    def start_camera_capture(self):
        if self.face_manager:
            self.face_manager.start_camera()
            self.face_manager.set_frame_callback(self.process_camera_frame)
    
    def stop_camera(self):
        self.camera_active = False
        self.start_button.configure(text="Start Camera")
        self.register_button.configure(state="disabled")
        
        if self.face_manager:
            self.face_manager.stop_camera()
    
    def process_camera_frame(self, frame, detected_faces):
        if self.camera_view:
            self.camera_view.update_frame(frame)
        
        # Update statistics
        known_count = sum(1 for face in detected_faces if face['status'] == 'known')
        unknown_count = sum(1 for face in detected_faces if face['status'] == 'unknown')
        
        self.update_statistics(known_count, unknown_count)
        self.update_face_info(len(detected_faces), known_count, unknown_count)
    
    def update_statistics(self, known_count, unknown_count):
        # Update present count
        today_attendance = self.attendance_manager.get_today_attendance() if self.attendance_manager else []
        self.present_count = len(today_attendance)
        
        # Update recognized faces
        self.recognized_count = known_count
        
        # Update unknown faces
        self.unknown_count = unknown_count
        
        # Update progress rings
        total_faces = known_count + unknown_count
        if total_faces > 0:
            self.present_ring.set_progress(min(100, (self.present_count / max(1, total_faces)) * 100))
            self.recognized_ring.set_progress(min(100, (known_count / total_faces) * 100))
            self.unknown_ring.set_progress(min(100, (unknown_count / total_faces) * 100))
        
        # Update labels
        # This would need to be updated to access the actual labels
        pass
    
    def update_face_info(self, total_faces, known_count, unknown_count):
        self.info_label.configure(text=f"Faces: {total_faces} | Known: {known_count} | Unknown: {unknown_count}")
    
    def update_attendance_display(self):
        if self.attendance_manager:
            today_attendance = self.attendance_manager.get_today_attendance()
            
            # Clear existing items
            for item in self.attendance_items:
                item.destroy()
            self.attendance_items = []
            
            # Add new items
            for record in today_attendance[-10:]:  # Show last 10 records
                item_frame = ctk.CTkFrame(
                    self.attendance_scroll,
                    fg_color="rgba(255, 255, 255, 0.1)",
                    corner_radius=8,
                    border_width=0
                )
                item_frame.pack(fill="x", padx=5, pady=2)
                
                name_label = ctk.CTkLabel(
                    item_frame,
                    text=record[1],  # name
                    font=("SF Pro Text", 12, "semibold"),
                    text_color=("white", "black")
                )
                name_label.pack(side="left", padx=10, pady=8)
                
                time_label = ctk.CTkLabel(
                    item_frame,
                    text=record[3],  # time
                    font=("SF Pro Text", 11),
                    text_color=("gray60", "gray40")
                )
                time_label.pack(side="left", padx=10)
                
                status_label = ctk.CTkLabel(
                    item_frame,
                    text=record[4],  # status
                    font=("SF Pro Text", 11),
                    text_color=("green" if record[4] == "Present" else "red", "green" if record[4] == "Present" else "red")
                )
                status_label.pack(side="right", padx=10, pady=8)
                
                self.attendance_items.append(item_frame)
    
    def show_registration_dialog(self):
        # This would open the registration dialog
        print("Show registration dialog")
    
    def refresh_data(self):
        # Update total users
        if self.face_manager:
            stats = self.face_manager.get_statistics()
            self.total_users = stats['known_faces_count']
            # Update total label
            # This would need to access the actual label
        
        # Update attendance display
        self.update_attendance_display()

class FaceDatabasePage(ctk.CTkFrame):
    def __init__(self, master, database_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.database_manager = database_manager
        self.theme_manager = ThemeManager()
        
        self.configure(fg_color="transparent")
        self.create_face_database_page()
    
    def create_face_database_page(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Search and filter section
        search_frame = ctk.CTkFrame(main_container, fg_color="transparent", corner_radius=0)
        search_frame.pack(fill="x", pady=(0, 20))
        
        search_entry = GlassEntry(
            search_frame,
            placeholder_text="Search users...",
            width=300
        )
        search_entry.pack(side="left", padx=(0, 10))
        
        add_button = GlassButton(
            search_frame,
            text="Add User",
            command=self.add_user_dialog,
            width=120
        )
        add_button.pack(side="right")
        
        # User list
        self.user_list = GlassListbox(main_container)
        self.user_list.pack(fill="both", expand=True)
        
        # Load users
        self.load_users()
    
    def load_users(self):
        if self.database_manager:
            users = self.database_manager.get_all_users()
            self.user_list.clear_items()
            
            for user in users:
                user_id, name, employee_id, department, face_image_path, _, _ = user
                display_text = f"{name} ({employee_id}) - {department}"
                self.user_list.add_item(display_text, lambda text: self.edit_user_dialog(text))
    
    def add_user_dialog(self):
        # This would open the add user dialog
        print("Add user dialog")
    
    def edit_user_dialog(self, user_text):
        # This would open the edit user dialog
        print(f"Edit user: {user_text}")

class AttendancePage(ctk.CTkFrame):
    def __init__(self, master, attendance_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.attendance_manager = attendance_manager
        self.theme_manager = ThemeManager()
        
        self.configure(fg_color="transparent")
        self.create_attendance_page()
    
    def create_attendance_page(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Date range selector
        date_frame = ctk.CTkFrame(main_container, fg_color="transparent", corner_radius=0)
        date_frame.pack(fill="x", pady=(0, 20))
        
        # Date filters
        daily_button = GlassButton(date_frame, text="Daily", width=100)
        daily_button.pack(side="left", padx=5)
        
        weekly_button = GlassButton(date_frame, text="Weekly", width=100)
        weekly_button.pack(side="left", padx=5)
        
        monthly_button = GlassButton(date_frame, text="Monthly", width=100)
        monthly_button.pack(side="left", padx=5)
        
        export_button = GlassButton(date_frame, text="Export CSV", width=120)
        export_button.pack(side="right", padx=5)
        
        # Attendance table
        self.attendance_table = ctk.CTkScrollableFrame(
            main_container,
            fg_color="rgba(255, 255, 255, 0.05)",
            corner_radius=15
        )
        self.attendance_table.pack(fill="both", expand=True)
        
        # Load attendance data
        self.load_attendance_data()
    
    def load_attendance_data(self):
        if self.attendance_manager:
            today = datetime.now().strftime('%Y-%m-%d')
            attendance_data = self.attendance_manager.get_attendance_by_date(today)
            
            # Clear existing data
            for widget in self.attendance_table.winfo_children():
                widget.destroy()
            
            # Display attendance records
            for record in attendance_data:
                name, date, time, status = record[1], record[2], record[3], record[4]
                
                item_frame = ctk.CTkFrame(
                    self.attendance_table,
                    fg_color="rgba(255, 255, 255, 0.1)",
                    corner_radius=8,
                    border_width=0
                )
                item_frame.pack(fill="x", padx=5, pady=2)
                
                ctk.CTkLabel(
                    item_frame,
                    text=name,
                    font=("SF Pro Text", 12),
                    text_color=("white", "black")
                ).pack(side="left", padx=10, pady=8)
                
                ctk.CTkLabel(
                    item_frame,
                    text=date,
                    font=("SF Pro Text", 11),
                    text_color=("gray60", "gray40")
                ).pack(side="left", padx=10)
                
                ctk.CTkLabel(
                    item_frame,
                    text=time,
                    font=("SF Pro Text", 11),
                    text_color=("gray60", "gray40")
                ).pack(side="left", padx=10)
                
                ctk.CTkLabel(
                    item_frame,
                    text=status,
                    font=("SF Pro Text", 11),
                    text_color=("green" if status == "Present" else "red", "green" if status == "Present" else "red")
                ).pack(side="right", padx=10, pady=8)

class ReportsPage(ctk.CTkFrame):
    def __init__(self, master, attendance_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.attendance_manager = attendance_manager
        self.theme_manager = ThemeManager()
        
        self.configure(fg_color="transparent")
        self.create_reports_page()
    
    def create_reports_page(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Report type selector
        selector_frame = ctk.CTkFrame(main_container, fg_color="transparent", corner_radius=0)
        selector_frame.pack(fill="x", pady=(0, 20))
        
        summary_button = GlassButton(selector_frame, text="Summary", width=100)
        summary_button.pack(side="left", padx=5)
        
        trends_button = GlassButton(selector_frame, text="Trends", width=100)
        trends_button.pack(side="left", padx=5)
        
        department_button = GlassButton(selector_frame, text="Department", width=100)
        department_button.pack(side="left", padx=5)
        
        # Report display area
        self.report_container = ctk.CTkFrame(
            main_container,
            fg_color="rgba(255, 255, 255, 0.05)",
            corner_radius=15
        )
        self.report_container.pack(fill="both", expand=True)
        
        # Load summary report
        self.load_summary_report()
    
    def load_summary_report(self):
        if self.attendance_manager:
            # Clear existing content
            for widget in self.report_container.winfo_children():
                widget.destroy()
            
            # Get attendance summary
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            summary = self.attendance_manager.get_attendance_summary(start_date, end_date)
            
            if summary:
                total_records, unique_users, present_count, absent_count = summary
                
                # Create summary cards
                cards_frame = ctk.CTkFrame(self.report_container, fg_color="transparent", corner_radius=0)
                cards_frame.pack(fill="x", padx=20, pady=20)
                
                # Total Records
                total_card = GlassCard(cards_frame)
                total_card.pack(side="left", fill="both", expand=True, padx=5)
                total_card.set_title("Total Records")
                ctk.CTkLabel(total_card, text=str(total_records), font=("SF Pro Display", 24, "bold")).pack(pady=10)
                
                # Unique Users
                users_card = GlassCard(cards_frame)
                users_card.pack(side="left", fill="both", expand=True, padx=5)
                users_card.set_title("Unique Users")
                ctk.CTkLabel(users_card, text=str(unique_users), font=("SF Pro Display", 24, "bold")).pack(pady=10)
                
                # Present Count
                present_card = GlassCard(cards_frame)
                present_card.pack(side="left", fill="both", expand=True, padx=5)
                present_card.set_title("Present")
                ctk.CTkLabel(present_card, text=str(present_count), font=("SF Pro Display", 24, "bold"), text_color=("green", "green")).pack(pady=10)
                
                # Absent Count
                absent_card = GlassCard(cards_frame)
                absent_card.pack(side="left", fill="both", expand=True, padx=5)
                absent_card.set_title("Absent")
                ctk.CTkLabel(absent_card, text=str(absent_count), font=("SF Pro Display", 24, "bold"), text_color=("red", "red")).pack(pady=10)

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.theme_manager = ThemeManager()
        
        self.configure(fg_color="transparent")
        self.create_settings_page()
    
    def create_settings_page(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Settings sections
        self.create_camera_settings(main_container)
        self.create_face_settings(main_container)
        self.create_database_settings(main_container)
        self.create_app_settings(main_container)
    
    def create_camera_settings(self, parent):
        camera_section = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        camera_section.pack(fill="x", pady=(0, 20))
        
        section_title = ctk.CTkLabel(
            camera_section,
            text="Camera Settings",
            font=("SF Pro Display", 16, "semibold"),
            text_color=("white", "black")
        )
        section_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Camera selection
        camera_frame = ctk.CTkFrame(camera_section, fg_color="rgba(255, 255, 255, 0.1)", corner_radius=10)
        camera_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            camera_frame,
            text="Camera Device:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(side="left", padx=10, pady=10)
        
        camera_selector = ctk.CTkOptionMenu(
            camera_frame,
            values=["Default", "Camera 1", "Camera 2"],
            font=("SF Pro Text", 12),
            width=150
        )
        camera_selector.pack(side="right", padx=10, pady=10)
    
    def create_face_settings(self, parent):
        face_section = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        face_section.pack(fill="x", pady=(0, 20))
        
        section_title = ctk.CTkLabel(
            face_section,
            text="Face Recognition Settings",
            font=("SF Pro Display", 16, "semibold"),
            text_color=("white", "black")
        )
        section_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Detection confidence
        detection_frame = ctk.CTkFrame(face_section, fg_color="rgba(255, 255, 255, 0.1)", corner_radius=10)
        detection_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            detection_frame,
            text="Detection Confidence:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(side="left", padx=10, pady=10)
        
        detection_slider = ctk.CTkSlider(
            detection_frame,
            from_=0.1,
            to=1.0,
            value=0.6,
            width=200
        )
        detection_slider.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            detection_frame,
            text="60%",
            font=("SF Pro Text", 12),
            text_color=("gray60", "gray40"),
            width=40
        ).pack(side="left", padx=10)
        
        # Recognition confidence
        recognition_frame = ctk.CTkFrame(face_section, fg_color="rgba(255, 255, 255, 0.1)", corner_radius=10)
        recognition_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            recognition_frame,
            text="Recognition Confidence:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(side="left", padx=10, pady=10)
        
        recognition_slider = ctk.CTkSlider(
            recognition_frame,
            from_=0.1,
            to=1.0,
            value=0.7,
            width=200
        )
        recognition_slider.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            recognition_frame,
            text="70%",
            font=("SF Pro Text", 12),
            text_color=("gray60", "gray40"),
            width=40
        ).pack(side="left", padx=10)
    
    def create_database_settings(self, parent):
        database_section = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        database_section.pack(fill="x", pady=(0, 20))
        
        section_title = ctk.CTkLabel(
            database_section,
            text="Database Settings",
            font=("SF Pro Display", 16, "semibold"),
            text_color=("white", "black")
        )
        section_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Auto backup
        backup_frame = ctk.CTkFrame(database_section, fg_color="rgba(255, 255, 255, 0.1)", corner_radius=10)
        backup_frame.pack(fill="x", padx=10, pady=5)
        
        backup_switch = ctk.CTkSwitch(
            backup_frame,
            text="Auto Backup Database",
            font=("SF Pro Text", 12),
            onvalue=True,
            offvalue=False
        )
        backup_switch.pack(side="left", padx=10, pady=10)
        
        # Cleanup old data
        cleanup_frame = ctk.CTkFrame(database_section, fg_color="rgba(255, 255, 255, 0.1)", corner_radius=10)
        cleanup_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            cleanup_frame,
            text="Keep attendance data for:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(side="left", padx=10, pady=10)
        
        cleanup_entry = GlassEntry(cleanup_frame, placeholder_text="365", width=80)
        cleanup_entry.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            cleanup_frame,
            text="days",
            font=("SF Pro Text", 12),
            text_color=("gray60", "gray40")
        ).pack(side="left", padx=5)
    
    def create_app_settings(self, parent):
        app_section = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        app_section.pack(fill="x")
        
        section_title = ctk.CTkLabel(
            app_section,
            text="Application Settings",
            font=("SF Pro Display", 16, "semibold"),
            text_color=("white", "black")
        )
        section_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Notifications
        notifications_frame = ctk.CTkFrame(app_section, fg_color="rgba(255, 255, 255, 0.1)", corner_radius=10)
        notifications_frame.pack(fill="x", padx=10, pady=5)
        
        notifications_switch = ctk.CTkSwitch(
            notifications_frame,
            text="Enable Notifications",
            font=("SF Pro Text", 12),
            onvalue=True,
            offvalue=False
        )
        notifications_switch.pack(side="left", padx=10, pady=10)
        
        # Auto start camera
        auto_start_frame = ctk.CTkFrame(app_section, fg_color="rgba(255, 255, 255, 0.1)", corner_radius=10)
        auto_start_frame.pack(fill="x", padx=10, pady=5)
        
        auto_start_switch = ctk.CTkSwitch(
            auto_start_frame,
            text="Auto Start Camera",
            font=("SF Pro Text", 12),
            onvalue=True,
            offvalue=False
        )
        auto_start_switch.pack(side="left", padx=10, pady=10)