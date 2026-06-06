import customtkinter as ctk
import threading
import time
from datetime import datetime
from database import DatabaseManager
from face_manager import FaceManager
from attendance_manager import AttendanceManager
from ui_components.theme import ThemeManager
from ui_components.sidebar import SidebarNavigation
from ui_components.pages import HomePage, FaceDatabasePage, AttendancePage, ReportsPage, SettingsPage

class FaceAttendanceApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Face Recognition Attendance System")
        self.root.geometry("1200x800")
        
        # Initialize managers
        self.database_manager = DatabaseManager()
        self.face_manager = FaceManager(self.database_manager)
        self.attendance_manager = AttendanceManager(self.database_manager)
        self.theme_manager = ThemeManager()
        
        # Application state
        self.current_page = "home"
        self.pages = {}
        
        # Configure window
        self.setup_window()
        
        # Create main layout
        self.create_main_layout()
        
        # Initialize pages
        self.initialize_pages()
        
        # Show home page by default
        self.show_page("home")
        
        # Start auto-refresh thread
        self.start_auto_refresh()
    
    def setup_window(self):
        """Setup main application window"""
        # Configure window properties
        self.root.minsize(1000, 700)
        
        # Set initial theme
        self.theme_manager.set_theme(self.theme_manager.DARK)
        
        # Configure window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_main_layout(self):
        """Create main application layout"""
        # Main container
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)
        
        # Create sidebar
        self.sidebar = SidebarNavigation(
            self.main_container,
            callback=self.on_navigation_change
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # Create content area
        self.content_container = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            corner_radius=0
        )
        self.content_container.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        # Create placeholder for pages
        self.content_placeholder = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent",
            corner_radius=0
        )
        self.content_placeholder.pack(fill="both", expand=True)
    
    def initialize_pages(self):
        """Initialize all application pages"""
        # Create pages
        self.pages["home"] = HomePage(
            self.content_placeholder,
            face_manager=self.face_manager,
            attendance_manager=self.attendance_manager
        )
        
        self.pages["faces"] = FaceDatabasePage(
            self.content_placeholder,
            database_manager=self.database_manager
        )
        
        self.pages["attendance"] = AttendancePage(
            self.content_placeholder,
            attendance_manager=self.attendance_manager
        )
        
        self.pages["reports"] = ReportsPage(
            self.content_placeholder,
            attendance_manager=self.attendance_manager
        )
        
        self.pages["settings"] = SettingsPage(
            self.content_placeholder
        )
        
        # Hide all pages initially
        for page in self.pages.values():
            page.pack_forget()
    
    def on_navigation_change(self, page_name):
        """Handle navigation change"""
        self.show_page(page_name)
    
    def show_page(self, page_name):
        """Show specific page"""
        if page_name in self.pages:
            # Hide current page
            if self.current_page in self.pages:
                self.pages[self.current_page].pack_forget()
            
            # Show new page
            self.pages[page_name].pack(fill="both", expand=True)
            self.current_page = page_name
            
            # Update sidebar
            self.sidebar.set_active_page(page_name)
            
            # Refresh page data
            self.refresh_page_data(page_name)
    
    def refresh_page_data(self, page_name):
        """Refresh data for specific page"""
        if page_name == "home":
            self.pages["home"].refresh_data()
        elif page_name == "faces":
            self.pages["faces"].load_users()
        elif page_name == "attendance":
            self.pages["attendance"].load_attendance_data()
        elif page_name == "reports":
            self.pages["reports"].load_summary_report()
    
    def start_auto_refresh(self):
        """Start auto-refresh thread"""
        def refresh_loop():
            while True:
                time.sleep(30)  # Refresh every 30 seconds
                if self.current_page == "home":
                    # Refresh home page data
                    self.root.after(0, self.pages["home"].refresh_data)
        
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
    
    def on_closing(self):
        """Handle application closing"""
        # Stop camera if active
        if self.face_manager:
            self.face_manager.stop_camera()
        
        # Close database connection
        if hasattr(self.database_manager, 'conn'):
            self.database_manager.conn.close()
        
        # Destroy window
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

class FaceRegistrationDialog:
    def __init__(self, parent, face_manager, callback):
        self.parent = parent
        self.face_manager = face_manager
        self.callback = callback
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Register New Person")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"400x500+{x}+{y}")
        
        self.create_dialog_content()
    
    def create_dialog_content(self):
        """Create dialog content"""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent", corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Register New Person",
            font=("SF Pro Display", 18, "semibold"),
            text_color=("white", "black")
        )
        title_label.pack(pady=(0, 20))
        
        # Form fields
        self.create_form_fields(main_frame)
        
        # Buttons
        self.create_action_buttons(main_frame)
        
        # Face preview (if available)
        self.create_face_preview(main_frame)
    
    def create_form_fields(self, parent):
        """Create form input fields"""
        fields_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        fields_frame.pack(fill="x", pady=(0, 20))
        
        # Full Name
        ctk.CTkLabel(
            fields_frame,
            text="Full Name:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(anchor="w", padx=(0, 0), pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter full name",
            font=("SF Pro Text", 12),
            width=300
        )
        self.name_entry.pack(fill="x", padx=(0, 0), pady=(0, 15))
        
        # Employee ID / Student ID
        ctk.CTkLabel(
            fields_frame,
            text="Employee ID / Student ID:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(anchor="w", padx=(0, 0), pady=(0, 5))
        
        self.id_entry = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter ID",
            font=("SF Pro Text", 12),
            width=300
        )
        self.id_entry.pack(fill="x", padx=(0, 0), pady=(0, 15))
        
        # Department
        ctk.CTkLabel(
            fields_frame,
            text="Department:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(anchor="w", padx=(0, 0), pady=(0, 5))
        
        self.department_entry = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter department",
            font=("SF Pro Text", 12),
            width=300
        )
        self.department_entry.pack(fill="x", padx=(0, 0), pady=(0, 15))
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        # Register button
        register_button = ctk.CTkButton(
            buttons_frame,
            text="Register Face",
            font=("SF Pro Text", 12, "semibold"),
            text_color=("white", "black"),
            fg_color="rgba(0, 132, 255, 0.8)",
            hover_color="rgba(0, 132, 255, 1)",
            width=140,
            height=35,
            command=self.register_person
        )
        register_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=("SF Pro Text", 12),
            text_color=("white", "black"),
            fg_color="rgba(255, 255, 255, 0.2)",
            hover_color="rgba(255, 255, 255, 0.3)",
            width=100,
            height=35,
            command=self.dialog.destroy
        )
        cancel_button.pack(side="left")
    
    def create_face_preview(self, parent):
        """Create face preview area"""
        preview_frame = ctk.CTkFrame(
            parent,
            fg_color="rgba(255, 255, 255, 0.1)",
            corner_radius=10,
            border_width=1,
            border_color="rgba(255, 255, 255, 0.2)"
        )
        preview_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        ctk.CTkLabel(
            preview_frame,
            text="Face Preview",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(pady=10)
        
        # Preview area (placeholder)
        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Face image will appear here",
            font=("SF Pro Text", 10),
            text_color=("gray60", "gray40"),
            width=200,
            height=150
        )
        self.preview_label.pack(pady=10)
    
    def register_person(self):
        """Register new person"""
        name = self.name_entry.get().strip()
        employee_id = self.id_entry.get().strip()
        department = self.department_entry.get().strip()
        
        if not name or not employee_id or not department:
            # Show error (you could implement a proper error dialog)
            print("Please fill in all fields")
            return
        
        # Get face from face manager (this would be implemented to get the latest unknown face)
        unknown_faces = self.face_manager.get_recent_unknown_faces(1)
        
        if not unknown_faces:
            print("No face image available for registration")
            return
        
        # Use the first unknown face
        face_data = unknown_faces[0]
        
        # Register the face
        success = self.face_manager.register_new_face(
            face_data['image'],
            name,
            employee_id,
            department
        )
        
        if success:
            # Close dialog
            self.dialog.destroy()
            
            # Call callback with success
            if self.callback:
                self.callback(True, name)
        else:
            print("Failed to register person")
            # Show error (you could implement a proper error dialog)

class UserManagementDialog:
    def __init__(self, parent, database_manager, user_data=None):
        self.parent = parent
        self.database_manager = database_manager
        self.user_data = user_data
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        title = "Edit User" if user_data else "Add User"
        self.dialog.title(title)
        self.dialog.geometry("400x450")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"400x450+{x}+{y}")
        
        self.create_dialog_content()
    
    def create_dialog_content(self):
        """Create dialog content"""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent", corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Edit User" if self.user_data else "Add User",
            font=("SF Pro Display", 18, "semibold"),
            text_color=("white", "black")
        )
        title_label.pack(pady=(0, 20))
        
        # Form fields
        self.create_form_fields(main_frame)
        
        # Buttons
        self.create_action_buttons(main_frame)
    
    def create_form_fields(self, parent):
        """Create form input fields"""
        fields_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        fields_frame.pack(fill="x", pady=(0, 20))
        
        # Full Name
        ctk.CTkLabel(
            fields_frame,
            text="Full Name:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(anchor="w", padx=(0, 0), pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter full name",
            font=("SF Pro Text", 12),
            width=300
        )
        self.name_entry.pack(fill="x", padx=(0, 0), pady=(0, 15))
        
        # Employee ID / Student ID
        ctk.CTkLabel(
            fields_frame,
            text="Employee ID / Student ID:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(anchor="w", padx=(0, 0), pady=(0, 5))
        
        self.id_entry = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter ID",
            font=("SF Pro Text", 12),
            width=300
        )
        self.id_entry.pack(fill="x", padx=(0, 0), pady=(0, 15))
        
        # Department
        ctk.CTkLabel(
            fields_frame,
            text="Department:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(anchor="w", padx=(0, 0), pady=(0, 5))
        
        self.department_entry = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter department",
            font=("SF Pro Text", 12),
            width=300
        )
        self.department_entry.pack(fill="x", padx=(0, 0), pady=(0, 15))
        
        # Face Image Path (read-only for editing)
        ctk.CTkLabel(
            fields_frame,
            text="Face Image:",
            font=("SF Pro Text", 12),
            text_color=("white", "black")
        ).pack(anchor="w", padx=(0, 0), pady=(0, 5))
        
        self.face_path_label = ctk.CTkLabel(
            fields_frame,
            text="No face image" if not self.user_data else "Face image loaded",
            font=("SF Pro Text", 10),
            text_color=("gray60", "gray40")
        )
        self.face_path_label.pack(fill="x", padx=(0, 0), pady=(0, 15))
        
        # Populate fields if editing existing user
        if self.user_data:
            user_id, name, employee_id, department, face_image_path, _, _ = self.user_data
            self.name_entry.insert(0, name)
            self.id_entry.insert(0, employee_id)
            self.department_entry.insert(0, department)
            if face_image_path:
                self.face_path_label.configure(text=face_image_path)
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        # Save button
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save",
            font=("SF Pro Text", 12, "semibold"),
            text_color=("white", "black"),
            fg_color="rgba(0, 132, 255, 0.8)",
            hover_color="rgba(0, 132, 255, 1)",
            width=100,
            height=35,
            command=self.save_user
        )
        save_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=("SF Pro Text", 12),
            text_color=("white", "black"),
            fg_color="rgba(255, 255, 255, 0.2)",
            hover_color="rgba(255, 255, 255, 0.3)",
            width=100,
            height=35,
            command=self.dialog.destroy
        )
        cancel_button.pack(side="left")
        
        # Delete button (only for editing)
        if self.user_data:
            delete_button = ctk.CTkButton(
                buttons_frame,
                text="Delete",
                font=("SF Pro Text", 12),
                text_color=("white", "black"),
                fg_color="rgba(255, 69, 58, 0.8)",
                hover_color="rgba(255, 69, 58, 1)",
                width=100,
                height=35,
                command=self.delete_user
            )
            delete_button.pack(side="left", padx=(10, 0))
    
    def save_user(self):
        """Save user data"""
        name = self.name_entry.get().strip()
        employee_id = self.id_entry.get().strip()
        department = self.department_entry.get().strip()
        
        if not name or not employee_id or not department:
            print("Please fill in all fields")
            return
        
        if self.user_data:
            # Update existing user
            user_id = self.user_data[0]
            success = self.database_manager.update_user(
                user_id, name, employee_id, department
            )
        else:
            # Add new user
            success = self.database_manager.add_user(name, employee_id, department)
        
        if success:
            self.dialog.destroy()
        else:
            print("Failed to save user")
    
    def delete_user(self):
        """Delete user"""
        if self.user_data:
            user_id = self.user_data[0]
            if self.database_manager.delete_user(user_id):
                self.dialog.destroy()

def main():
    """Main entry point"""
    try:
        app = FaceAttendanceApp()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main()