import cv2
import customtkinter as ctk
from PIL import Image

from attendance_manager import AttendanceManager
from database import DatabaseManager
from face_manager import FaceManager
from ui_components.pages import (
    AttendancePage,
    FaceDatabasePage,
    HomePage,
    LiveAttendancePage,
    ReportsPage,
    SettingsPage,
)
from ui_components.sidebar import SidebarNavigation
from ui_components.theme import ThemeManager
from ui_components.widgets import GlassButton, GlassEntry, colors


class FaceAttendanceApp:
    def __init__(self, start_camera=False):
        self.root = ctk.CTk()
        self.root.title("Face Attendance Studio")
        self.root.geometry("1360x860")
        self.root.minsize(1120, 740)

        self.theme_manager = ThemeManager()
        self.theme_manager.set_theme(ThemeManager.DARK)

        self.database_manager = DatabaseManager()
        self.attendance_manager = AttendanceManager(self.database_manager)
        self.face_manager = FaceManager(self.database_manager)
        self.face_manager.set_attendance_callback(self.attendance_manager.mark_attendance)

        self.current_page = None
        self.pages = {}
        self.registration_dialog = None
        self._closing = False
        self._theme_rebuild_active = False

        self.setup_window()
        self.create_layout()
        self.initialize_pages()
        self.show_page("home")
        self.schedule_refresh()

        if start_camera:
            self.face_manager.start_camera()

    def setup_window(self):
        self.root.configure(fg_color=self.theme_manager.get_color("window"))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.theme_manager.add_listener(self.on_theme_change)

    def create_layout(self):
        palette = colors()
        self.main_container = ctk.CTkFrame(self.root, fg_color=palette["window"], corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        self.sidebar = SidebarNavigation(
            self.main_container,
            callback=self.on_navigation_change,
            theme_manager=self.theme_manager,
        )
        self.sidebar.pack(side="left", fill="y")

        self.content_container = ctk.CTkFrame(self.main_container, fg_color=palette["window"], corner_radius=0)
        self.content_container.pack(side="right", fill="both", expand=True)

    def initialize_pages(self):
        common_camera_args = {
            "face_manager": self.face_manager,
            "attendance_manager": self.attendance_manager,
            "open_registration_callback": self.open_registration_dialog,
            "theme_manager": self.theme_manager,
        }

        self.pages = {
            "home": HomePage(self.content_container, **common_camera_args),
            "live": LiveAttendancePage(self.content_container, **common_camera_args),
            "attendance": AttendancePage(
                self.content_container,
                attendance_manager=self.attendance_manager,
                theme_manager=self.theme_manager,
            ),
            "faces": FaceDatabasePage(
                self.content_container,
                database_manager=self.database_manager,
                face_manager=self.face_manager,
                open_registration_callback=self.open_registration_dialog,
                on_faces_changed=self.refresh_all_pages,
                theme_manager=self.theme_manager,
            ),
            "reports": ReportsPage(
                self.content_container,
                attendance_manager=self.attendance_manager,
                face_manager=self.face_manager,
                theme_manager=self.theme_manager,
            ),
            "settings": SettingsPage(
                self.content_container,
                face_manager=self.face_manager,
                attendance_manager=self.attendance_manager,
                on_reset=self.refresh_all_pages,
                theme_manager=self.theme_manager,
            ),
        }

        for page in self.pages.values():
            page.pack_forget()

    def on_navigation_change(self, page_name):
        self.show_page(page_name)

    def show_page(self, page_name):
        if page_name not in self.pages:
            return

        if self.current_page in self.pages:
            old_page = self.pages[self.current_page]
            if hasattr(old_page, "on_hide"):
                old_page.on_hide()
            old_page.pack_forget()

        page = self.pages[page_name]
        page.pack(fill="both", expand=True)
        self.current_page = page_name
        self.sidebar.set_active_page(page_name)
        self.animate_page_in(page)

        if hasattr(page, "on_show"):
            page.on_show()

    def animate_page_in(self, page, step=0):
        if not page.winfo_exists():
            return
        palette = colors()
        sequence = [palette["window_alt"], palette["window"]]
        page.configure(fg_color=sequence[min(step, len(sequence) - 1)])
        if step < len(sequence) - 1:
            self.root.after(45, lambda: self.animate_page_in(page, step + 1))

    def open_registration_dialog(self):
        if self.registration_dialog and self.registration_dialog.exists():
            self.registration_dialog.lift()
            return

        self.face_manager.set_registering(True)
        self.registration_dialog = FaceRegistrationDialog(
            self.root,
            self.face_manager,
            on_saved=self.on_registration_saved,
            on_closed=self.on_registration_closed,
        )

    def on_registration_saved(self, _name):
        self.face_manager.refresh_faces()
        self.refresh_all_pages()

    def refresh_all_pages(self):
        for page_name in ("home", "live", "faces"):
            page = self.pages.get(page_name)
            if hasattr(page, "refresh_data"):
                page.refresh_data()
            if hasattr(page, "load_users"):
                page.load_users()
        for page_name in ("attendance", "reports"):
            page = self.pages.get(page_name)
            if hasattr(page, "load_attendance_data"):
                page.load_attendance_data()
            if hasattr(page, "load_summary_report"):
                page.load_summary_report()

    def on_registration_closed(self):
        self.face_manager.set_registering(False)
        self.registration_dialog = None

    def schedule_refresh(self):
        if self._closing:
            return
        page = self.pages.get(self.current_page)
        if page and hasattr(page, "refresh_data"):
            page.refresh_data()
        self.root.after(30000, self.schedule_refresh)

    def on_theme_change(self, _theme, palette):
        self.root.configure(fg_color=palette["window"])
        self.main_container.configure(fg_color=palette["window"])
        self.content_container.configure(fg_color=palette["window"])
        if self._theme_rebuild_active or not self.pages:
            return

        current_page = self.current_page or "home"
        self._theme_rebuild_active = True
        try:
            if self.face_manager:
                self.face_manager.set_frame_callback(None)
            for page in self.pages.values():
                page.destroy()
            self.pages = {}
            self.current_page = None
            self.initialize_pages()
            self.show_page(current_page)
        finally:
            self._theme_rebuild_active = False

    def on_closing(self):
        self._closing = True
        if self.registration_dialog and self.registration_dialog.exists():
            self.registration_dialog.close()
        self.face_manager.shutdown()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    def after(self, *args, **kwargs):
        return self.root.after(*args, **kwargs)

    def mainloop(self):
        return self.run()

    def destroy(self):
        return self.on_closing()


class FaceRegistrationDialog:
    def __init__(self, parent, face_manager, on_saved=None, on_closed=None):
        self.parent = parent
        self.face_manager = face_manager
        self.on_saved = on_saved
        self.on_closed = on_closed
        self.captured_face = None
        self.preview_image = None
        self.current_image = None
        self.saved = False
        self._closed = False

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Register Face")
        self.dialog.resizable(False, False)
        self.dialog.attributes("-alpha", 0.0)
        self.dialog.withdraw()
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
        self.create_content()
        self.center_dialog()
        self.dialog.deiconify()
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.focus_force()
        self.animate_popup()

    def exists(self):
        try:
            return bool(self.dialog.winfo_exists())
        except Exception:
            return False

    def lift(self):
        self.dialog.lift()
        self.dialog.focus_force()

    def center_dialog(self):
        width = 620
        height = 720
        self.dialog.update_idletasks()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = max((screen_width - width) // 2, 20)
        y = max((screen_height - height) // 2, 20)
        if x + width > screen_width - 20:
            x = max(screen_width - width - 20, 0)
        if y + height > screen_height - 20:
            y = max(screen_height - height - 20, 0)
        self.target_geometry = (width, height, x, y)
        self.dialog.geometry(f"{width - 28}x{height - 28}+{x + 14}+{y + 14}")

    def animate_popup(self, step=0):
        if not self.exists():
            return
        width, height, x, y = self.target_geometry
        steps = 7
        progress = min(1.0, step / steps)
        current_width = int((width - 28) + (28 * progress))
        current_height = int((height - 28) + (28 * progress))
        current_x = int((x + 14) - (14 * progress))
        current_y = int((y + 14) - (14 * progress))
        self.dialog.geometry(f"{current_width}x{current_height}+{current_x}+{current_y}")
        self.dialog.attributes("-alpha", min(1.0, 0.15 + (0.85 * progress)))
        if step < steps:
            self.dialog.after(16, lambda: self.animate_popup(step + 1))

    def create_content(self):
        palette = colors()
        self.dialog.configure(fg_color=palette["window"])

        container = ctk.CTkFrame(
            self.dialog,
            fg_color=palette["glass"],
            corner_radius=24,
            border_width=1,
            border_color=palette["border"],
        )
        container.pack(fill="both", expand=True, padx=20, pady=18)

        footer = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0)
        footer.pack(fill="x", side="bottom", padx=18, pady=(8, 18))

        self.capture_button = GlassButton(
            footer,
            text="Capture Photo",
            width=142,
            variant="primary",
            command=self.capture_photo,
        )
        self.capture_button.pack(side="left", padx=(0, 10))

        self.save_button = GlassButton(footer, text="Save", width=100, variant="success", command=self.save)
        self.save_button.pack(side="left", padx=(0, 10))

        self.cancel_button = GlassButton(footer, text="Cancel", width=100, variant="secondary", command=self.close)
        self.cancel_button.pack(side="left")

        print("REGISTER POPUP BUTTONS CREATED: Capture Photo, Save, Cancel")

        ctk.CTkLabel(
            container,
            text="Register Face",
            font=("SF Pro Display", 26, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 0))
        ctk.CTkLabel(
            container,
            text="Capture a clear photo to register this person",
            font=("SF Pro Text", 12),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", padx=18, pady=(4, 14))

        preview_card = ctk.CTkFrame(
            container,
            fg_color=palette["glass"],
            corner_radius=18,
            border_width=1,
            border_color=palette["border_soft"],
            height=180,
        )
        preview_card.pack(fill="x", padx=18, pady=(0, 14))
        preview_card.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(
            preview_card,
            text="Photo preview",
            font=("SF Pro Display", 16, "bold"),
            text_color=palette["text_muted"],
            fg_color="#05070B",
            corner_radius=14,
        )
        self.preview_label.pack(fill="both", expand=True, padx=14, pady=14)

        form = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0)
        form.pack(fill="x", padx=18, pady=(0, 8))

        self.name_entry = self.field(form, "Name", "Full name")
        self.student_id_entry = self.field(form, "Student ID", "Student ID")
        self.department_entry = self.field(form, "Department", "Department")

        self.message_label = ctk.CTkLabel(
            container,
            text="",
            font=("SF Pro Text", 12, "bold"),
            text_color=palette["text_muted"],
            anchor="w",
        )
        self.message_label.pack(fill="x", padx=18, pady=(4, 6))

    def field(self, parent, label, placeholder):
        palette = colors()
        ctk.CTkLabel(
            parent,
            text=label,
            font=("SF Pro Text", 12, "bold"),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(0, 5))
        entry = GlassEntry(parent, placeholder_text=placeholder)
        entry.configure(height=38)
        entry.pack(fill="x", pady=(0, 10))
        return entry

    def capture_photo(self):
        capture, message = self.face_manager.capture_registration_face()
        if capture is None:
            self.show_message(message, "warning")
            return

        self.captured_face = capture["face_image"]
        self.show_preview(self.captured_face)
        self.show_message(message, "success")

    def show_preview(self, face_image):
        image_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image_rgb)
        image.thumbnail((540, 142), Image.Resampling.LANCZOS)
        self.current_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        self.preview_image = self.current_image
        self.preview_label.configure(image=self.current_image, text="")

    def save(self):
        name = self.name_entry.get().strip()
        student_id = self.student_id_entry.get().strip()
        department = self.department_entry.get().strip()

        if self.captured_face is None:
            self.show_message("Capture a face photo first.", "warning")
            return

        self.save_button.configure(state="disabled")
        success, message, _profile_path = self.face_manager.register_face(
            self.captured_face,
            name,
            student_id,
            department,
        )

        if success:
            self.saved = True
            self.save_button.configure(state="disabled")
            if self.on_saved:
                self.on_saved(name)
            self.close()
            return

        self.save_button.configure(state="normal")
        self.show_message(message, "danger")

    def show_message(self, message, tone="neutral"):
        palette = colors()
        color = {
            "success": palette["success"],
            "warning": palette["warning"],
            "danger": palette["danger"],
            "neutral": palette["text_muted"],
        }.get(tone, palette["text_muted"])
        self.message_label.configure(text=message, text_color=color)

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.dialog.grab_release()
        except Exception:
            pass
        self.dialog.destroy()
        if self.on_closed:
            self.on_closed()


def main():
    try:
        app = FaceAttendanceApp()
        app.run()
    except Exception as exc:
        print(f"Error starting application: {exc}")
        print("Install dependencies with: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
