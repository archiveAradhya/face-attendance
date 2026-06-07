import os
from datetime import datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk

from .theme import ThemeManager
from .widgets import (
    SPACING,
    CameraView,
    GlassButton,
    GlassCard,
    GlassEntry,
    GlassImage,
    MetricCard,
    StatusBadge,
    colors,
    row_frame,
)


def clear_children(widget):
    for child in widget.winfo_children():
        child.destroy()


def attendance_parts(record):
    return {
        "id": record[0],
        "user_id": record[1],
        "name": record[2],
        "date": record[3],
        "time": record[4],
        "status": record[5],
        "student_id": record[7] if len(record) > 7 else "",
        "department": record[8] if len(record) > 8 else "",
    }


class HomePage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        face_manager=None,
        attendance_manager=None,
        open_registration_callback=None,
        theme_manager=None,
        page_title="Welcome back",
        page_subtitle="Attendance overview, daily status, and recognition summary.",
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.face_manager = face_manager
        self.attendance_manager = attendance_manager
        self.open_registration_callback = open_registration_callback
        self.theme_manager = theme_manager or ThemeManager()
        self.page_title = page_title
        self.page_subtitle = page_subtitle

        self._latest_frame = None
        self._latest_faces = []
        self._ui_update_pending = False
        self._last_list_refresh = 0

        self.configure(fg_color=self.theme_manager.get_color("window"))
        self.create_page()

    def create_page(self):
        palette = colors()
        self.container = ctk.CTkFrame(self, fg_color=palette["window"], corner_radius=0)
        self.container.pack(fill="both", expand=True, padx=SPACING["outer"], pady=SPACING["outer"])

        self.create_header(self.container)
        self.create_metric_cards(self.container)

        body = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True, pady=(SPACING["card"], 0))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self.create_camera_card(body)
        self.create_today_panel(body)

    def create_header(self, parent):
        palette = colors()
        header = ctk.CTkFrame(
            parent,
            fg_color=palette["glass_subtle"],
            corner_radius=24,
            border_width=1,
            border_color=palette["border_soft"],
        )
        header.pack(fill="x", pady=(0, 24))

        title_block = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        title_block.pack(side="left", fill="x", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            title_block,
            text=self.page_title,
            font=("SF Pro Display", 30, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            title_block,
            text=f"{self.page_subtitle}  {datetime.now().strftime('%A, %B %d, %Y')}",
            font=("SF Pro Text", 13),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        self.camera_badge = StatusBadge(header, "online" if self._camera_active() else "offline")
        self.camera_badge.pack(side="right", padx=18, pady=16)

    def create_camera_card(self, parent):
        palette = colors()
        camera_card = GlassCard(parent, title="Camera Preview")
        camera_card.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["card"]))

        self.camera_view = CameraView(camera_card.content, height=250)
        self.camera_view.pack(fill="both", expand=True)

        self.face_status_label = ctk.CTkLabel(
            camera_card.content,
            text="Open Live Attendance to control the camera",
            font=("SF Pro Text", 13, "bold"),
            text_color=palette["text_muted"],
            anchor="center",
        )
        self.face_status_label.pack(fill="x", pady=(SPACING["inner"], 0))
        self.update_camera_buttons()

    def create_today_panel(self, parent):
        self.today_card = GlassCard(parent, title="Today Attendance")
        self.today_card.grid(row=0, column=1, sticky="nsew")

        self.today_list = ctk.CTkScrollableFrame(
            self.today_card.content,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=colors()["surface_hover"],
            scrollbar_fg_color=colors()["surface"],
        )
        self.today_list.pack(fill="both", expand=True)

    def create_metric_cards(self, parent):
        metrics = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        metrics.pack(fill="x")

        for column in range(4):
            metrics.grid_columnconfigure(column, weight=1, uniform="metric")

        self.present_metric = MetricCard(metrics, "Present Today", "0", "success")
        self.present_metric.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.recognized_metric = MetricCard(metrics, "Recognized", "0", "accent")
        self.recognized_metric.grid(row=0, column=1, sticky="ew", padx=8)

        self.unknown_metric = MetricCard(metrics, "Unknown", "0", "warning")
        self.unknown_metric.grid(row=0, column=2, sticky="ew", padx=8)

        self.total_metric = MetricCard(metrics, "Total Registered", "0", "text")
        self.total_metric.grid(row=0, column=3, sticky="ew", padx=(8, 0))

    def on_show(self):
        if self.face_manager:
            self.face_manager.set_frame_callback(self.process_camera_frame)
        self.refresh_data()
        self.update_camera_buttons()
        if not self._camera_active():
            self.camera_view.show_placeholder()

    def on_hide(self):
        if self.face_manager:
            self.face_manager.set_frame_callback(None)

    def _camera_active(self):
        return bool(self.face_manager and self.face_manager.running)

    def start_camera(self):
        if not self.face_manager:
            return
        self.face_manager.set_frame_callback(self.process_camera_frame)
        self.face_manager.start_camera(0)
        self.update_camera_buttons()
        self.after(700, self.check_camera_started)

    def check_camera_started(self):
        if not self.face_manager:
            return
        if self.face_manager.running:
            return
        error = self.face_manager.last_error or "Unable to open camera 0"
        self.camera_view.show_placeholder(error)
        self.face_status_label.configure(text=error)
        self.camera_badge.set_status("error")
        self.update_camera_buttons()

    def stop_camera(self):
        if self.face_manager:
            self.face_manager.stop_camera()
        self.camera_view.show_placeholder()
        self.update_camera_buttons()

    def update_camera_buttons(self):
        active = self._camera_active()
        if hasattr(self, "start_button"):
            self.start_button.configure(state="disabled" if active else "normal")
        if hasattr(self, "stop_button"):
            self.stop_button.configure(state="normal" if active else "disabled")
        if hasattr(self, "camera_view"):
            self.camera_view.set_active(active)
        self.camera_badge.set_status("online" if active else "offline")

    def open_registration(self):
        if self.open_registration_callback:
            self.open_registration_callback()

    def process_camera_frame(self, frame, detected_faces):
        self._latest_frame = frame.copy()
        self._latest_faces = list(detected_faces)
        if not self._ui_update_pending:
            self._ui_update_pending = True
            try:
                self.after(0, self.apply_camera_update)
            except Exception:
                self._ui_update_pending = False

    def apply_camera_update(self):
        self._ui_update_pending = False
        if not self.winfo_exists():
            return
        if self._latest_frame is None:
            return
        if not self._camera_active():
            self.camera_view.show_placeholder()
            self.face_status_label.configure(text="Camera is Off")
            self.camera_badge.set_status("offline")
            return

        self.camera_view.update_frame(self._latest_frame)
        known_count = sum(1 for face in self._latest_faces if face.get("status") == "known")
        unknown_count = sum(1 for face in self._latest_faces if face.get("status") == "unknown")
        checking_count = sum(1 for face in self._latest_faces if face.get("status") == "checking")
        self.face_status_label.configure(
            text=f"Faces {len(self._latest_faces)}  •  Recognized {known_count}  •  Unknown {unknown_count}"
        )
        self.camera_badge.set_status("checking" if checking_count else "online")

        now = datetime.now().timestamp()
        if now - self._last_list_refresh > 2:
            self._last_list_refresh = now
            self.refresh_data()

    def refresh_data(self):
        today_records = self.attendance_manager.get_today_attendance() if self.attendance_manager else []
        stats = self.face_manager.get_statistics() if self.face_manager else {}

        self.present_metric.set_value(len(today_records))
        self.recognized_metric.set_value(stats.get("recognized_count", 0))
        self.unknown_metric.set_value(stats.get("unknown_faces_count", 0))
        self.total_metric.set_value(stats.get("known_faces_count", 0))

        self.render_today_attendance(today_records)

    def render_today_attendance(self, records):
        palette = colors()
        clear_children(self.today_list)

        if not records:
            ctk.CTkLabel(
                self.today_list,
                text="No attendance marked today",
                font=("SF Pro Text", 13, "bold"),
                text_color=palette["text_muted"],
            ).pack(fill="x", pady=24)
            return

        for record in records[-12:][::-1]:
            item = attendance_parts(record)
            row = row_frame(self.today_list)
            row.pack(fill="x", pady=5)

            left = ctk.CTkFrame(row, fg_color="transparent", corner_radius=0)
            left.pack(side="left", fill="x", expand=True, padx=12, pady=10)

            ctk.CTkLabel(
                left,
                text=item["name"],
                font=("SF Pro Text", 13, "bold"),
                text_color=palette["text"],
                anchor="w",
            ).pack(fill="x")
            ctk.CTkLabel(
                left,
                text=f"{item['student_id']} • {item['department']}",
                font=("SF Pro Text", 11),
                text_color=palette["text_muted"],
                anchor="w",
            ).pack(fill="x", pady=(2, 0))

            ctk.CTkLabel(
                row,
                text=item["time"],
                font=("SF Pro Text", 12, "bold"),
                text_color=palette["success"],
            ).pack(side="right", padx=12)


class LiveAttendancePage(HomePage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("page_title", "Live Attendance")
        kwargs.setdefault("page_subtitle", "Monitor face boxes, recognition status, and attendance capture.")
        super().__init__(*args, **kwargs)

    def create_page(self):
        palette = colors()
        self.container = ctk.CTkFrame(self, fg_color=palette["window"], corner_radius=0)
        self.container.pack(fill="both", expand=True, padx=SPACING["outer"], pady=SPACING["outer"])

        self.create_header(self.container)

        body = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=340)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, minsize=132)

        self.create_live_camera_card(body)
        self.create_today_panel(body)

        metrics = ctk.CTkFrame(body, fg_color="transparent", corner_radius=0)
        metrics.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(SPACING["card"], 0))
        self.create_metric_cards(metrics)

    def create_live_camera_card(self, parent):
        palette = colors()
        camera_card = GlassCard(parent, title="Live Camera Feed")
        camera_card.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["card"]))

        self.camera_view = CameraView(camera_card.content, height=460)
        self.camera_view.pack(fill="both", expand=True)

        controls = ctk.CTkFrame(camera_card.content, fg_color="transparent", corner_radius=0)
        controls.pack(fill="x", pady=(SPACING["inner"], 0))

        self.start_button = GlassButton(controls, text="Start Camera", width=126, command=self.start_camera)
        self.start_button.pack(side="left", padx=(0, 10))

        self.stop_button = GlassButton(
            controls,
            text="Stop Camera",
            width=120,
            variant="secondary",
            command=self.stop_camera,
        )
        self.stop_button.pack(side="left", padx=(0, 10))

        self.register_button = GlassButton(
            controls,
            text="Register Face",
            width=142,
            variant="success",
            command=self.open_registration,
        )
        self.register_button.pack(side="left", padx=(0, 10))

        self.face_status_label = ctk.CTkLabel(
            controls,
            text="Faces 0  •  Ready",
            font=("SF Pro Text", 13, "bold"),
            text_color=palette["text_muted"],
            anchor="e",
        )
        self.face_status_label.pack(side="right", fill="x", expand=True)
        self.update_camera_buttons()


class FaceDatabasePage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        database_manager=None,
        face_manager=None,
        open_registration_callback=None,
        on_faces_changed=None,
        theme_manager=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.database_manager = database_manager
        self.face_manager = face_manager
        self.open_registration_callback = open_registration_callback
        self.on_faces_changed = on_faces_changed
        self.theme_manager = theme_manager or ThemeManager()
        self.search_var = ctk.StringVar(value="")
        self.toast = None

        self.configure(fg_color=self.theme_manager.get_color("window"))
        self.create_page()

    def create_page(self):
        palette = colors()
        container = ctk.CTkFrame(self, fg_color=palette["window"], corner_radius=0)
        container.pack(fill="both", expand=True, padx=SPACING["outer"], pady=SPACING["outer"])

        self.create_header(container, "Face Database", "Registered profiles saved from live camera captures.")

        toolbar = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0)
        toolbar.pack(fill="x", pady=(SPACING["card"], SPACING["inner"]))

        self.search_entry = GlassEntry(
            toolbar,
            placeholder_text="Search by name, ID, or department",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_users())

        GlassButton(
            toolbar,
            text="Register Face",
            width=142,
            variant="success",
            command=self.open_registration_callback,
        ).pack(side="right")

        self.user_list = ctk.CTkScrollableFrame(
            container,
            fg_color=palette["glass_subtle"],
            corner_radius=18,
            border_width=1,
            border_color=palette["border_soft"],
            scrollbar_button_color=palette["surface_hover"],
            scrollbar_fg_color=palette["surface"],
        )
        self.user_list.pack(fill="both", expand=True)
        self.load_users()

    def create_header(self, parent, title, subtitle):
        palette = colors()
        ctk.CTkLabel(
            parent,
            text=title,
            font=("SF Pro Display", 30, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            parent,
            text=subtitle,
            font=("SF Pro Text", 13),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

    def on_show(self):
        self.load_users()

    def load_users(self):
        if not self.database_manager:
            return

        palette = colors()
        query = self.search_var.get().strip().lower()
        clear_children(self.user_list)

        users = self.database_manager.get_all_users()
        if query:
            users = [
                user
                for user in users
                if query in " ".join(str(value or "") for value in user[1:5]).lower()
            ]

        if not users:
            ctk.CTkLabel(
                self.user_list,
                text="No registered faces yet\nUse Register Face to add a profile.",
                font=("SF Pro Text", 14, "bold"),
                text_color=palette["text_muted"],
                justify="center",
            ).pack(pady=28)
            return

        for user in users:
            user_id, name, student_id, department, face_image_path, created_at, _ = user
            row = row_frame(self.user_list)
            row.pack(fill="x", padx=8, pady=6)

            if face_image_path and os.path.exists(face_image_path):
                avatar = GlassImage(row, image_path=face_image_path, size=(58, 58), width=66, height=66)
            else:
                avatar = ctk.CTkLabel(
                    row,
                    text=name[:1].upper(),
                    width=66,
                    height=66,
                    corner_radius=14,
                    fg_color=palette["accent_soft"],
                    text_color=palette["accent"],
                    font=("SF Pro Display", 24, "bold"),
                )
            avatar.pack(side="left", padx=12, pady=10)

            info = ctk.CTkFrame(row, fg_color="transparent", corner_radius=0)
            info.pack(side="left", fill="x", expand=True, pady=10)

            ctk.CTkLabel(
                info,
                text=name,
                font=("SF Pro Text", 15, "bold"),
                text_color=palette["text"],
                anchor="w",
            ).pack(fill="x")
            ctk.CTkLabel(
                info,
                text=f"{student_id} • {department or 'No department'}",
                font=("SF Pro Text", 12),
                text_color=palette["text_muted"],
                anchor="w",
            ).pack(fill="x", pady=(3, 0))

            ctk.CTkLabel(
                info,
                text=f"Added {created_at[:10] if created_at else 'recently'}",
                font=("SF Pro Text", 12),
                text_color=palette["text_dim"],
                anchor="w",
            ).pack(fill="x", pady=(4, 0))

            GlassButton(
                row,
                text="Delete",
                width=92,
                variant="danger",
                command=lambda selected=user: self.confirm_delete_user(selected),
            ).pack(side="right", padx=12, pady=12)

    def confirm_delete_user(self, user):
        palette = colors()
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Delete Face")
        dialog.geometry("360x190")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        card = ctk.CTkFrame(
            dialog,
            fg_color=palette["glass"],
            corner_radius=18,
            border_width=1,
            border_color=palette["border"],
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            card,
            text="Delete this registered face?",
            font=("SF Pro Display", 18, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 4))
        ctk.CTkLabel(
            card,
            text=user[1],
            font=("SF Pro Text", 13),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", padx=18)

        actions = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        actions.pack(fill="x", side="bottom", padx=18, pady=18)
        GlassButton(actions, text="Cancel", width=100, variant="secondary", command=dialog.destroy).pack(
            side="right"
        )
        GlassButton(
            actions,
            text="Delete",
            width=100,
            variant="danger",
            command=lambda: self.delete_user(user, dialog),
        ).pack(side="right", padx=(0, 10))

    def delete_user(self, user, dialog):
        if self.face_manager:
            deleted = self.face_manager.delete_registered_face(user[0])
        elif self.database_manager:
            deleted = self.database_manager.delete_user(user[0])
        else:
            deleted = False

        dialog.destroy()
        if deleted:
            self.load_users()
            if self.on_faces_changed:
                self.on_faces_changed()
            self.show_toast("Face deleted successfully")
        else:
            self.show_toast("Could not delete face", tone="danger")

    def show_toast(self, message, tone="success"):
        palette = colors()
        if self.toast and self.toast.winfo_exists():
            self.toast.destroy()

        bg = palette["success_soft"] if tone == "success" else palette["danger_soft"]
        fg = palette["success"] if tone == "success" else palette["danger"]
        self.toast = ctk.CTkLabel(
            self,
            text=message,
            font=("SF Pro Text", 13, "bold"),
            text_color=fg,
            fg_color=bg,
            corner_radius=14,
        )
        self.toast.place(relx=1.0, x=-24, y=24, anchor="ne")
        self.toast.after(2600, self.toast.destroy)


class AttendancePage(ctk.CTkFrame):
    def __init__(self, master, attendance_manager=None, theme_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        self.attendance_manager = attendance_manager
        self.theme_manager = theme_manager or ThemeManager()
        self.search_var = ctk.StringVar(value="")

        self.configure(fg_color=self.theme_manager.get_color("window"))
        self.create_page()

    def create_page(self):
        palette = colors()
        container = ctk.CTkFrame(self, fg_color=palette["window"], corner_radius=0)
        container.pack(fill="both", expand=True, padx=SPACING["outer"], pady=SPACING["outer"])

        ctk.CTkLabel(
            container,
            text="Attendance Records",
            font=("SF Pro Display", 30, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            container,
            text="Daily recognition records. Attendance is marked once per person per day.",
            font=("SF Pro Text", 13),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        toolbar = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0)
        toolbar.pack(fill="x", pady=(SPACING["card"], SPACING["inner"]))

        self.search_entry = GlassEntry(
            toolbar,
            placeholder_text="Search attendance by name, ID, department, or status",
            textvariable=self.search_var,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_attendance_data())

        GlassButton(toolbar, text="Clear Attendance", width=154, variant="danger", command=self.clear_attendance).pack(
            side="right"
        )

        self.table = ctk.CTkScrollableFrame(
            container,
            fg_color=palette["glass_subtle"],
            corner_radius=18,
            border_width=1,
            border_color=palette["border_soft"],
            scrollbar_button_color=palette["surface_hover"],
            scrollbar_fg_color=palette["surface"],
        )
        self.table.pack(fill="both", expand=True)
        self.load_attendance_data()

    def on_show(self):
        self.load_attendance_data()

    def load_attendance_data(self):
        if not self.attendance_manager:
            return

        palette = colors()
        clear_children(self.table)
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.attendance_manager.get_attendance_by_date(today)
        query = self.search_var.get().strip().lower()
        if query:
            records = [
                record
                for record in records
                if query in " ".join(str(value or "") for value in attendance_parts(record).values()).lower()
            ]

        header = ctk.CTkFrame(self.table, fg_color="transparent", corner_radius=0)
        header.pack(fill="x", padx=12, pady=(12, 4))
        for text, width in [("Name", 220), ("Student ID", 160), ("Department", 190), ("Time", 110), ("Status", 100)]:
            ctk.CTkLabel(
                header,
                text=text,
                width=width,
                font=("SF Pro Text", 12, "bold"),
                text_color=palette["text_dim"],
                anchor="w",
            ).pack(side="left", padx=6)

        if not records:
            ctk.CTkLabel(
                self.table,
                text="No matching attendance records" if query else "No records for today",
                font=("SF Pro Text", 14, "bold"),
                text_color=palette["text_muted"],
            ).pack(pady=32)
            return

        for record in records[::-1]:
            item = attendance_parts(record)
            row = row_frame(self.table)
            row.pack(fill="x", padx=12, pady=5)
            values = [
                (item["name"], 220, palette["text"]),
                (item["student_id"], 160, palette["text_muted"]),
                (item["department"], 190, palette["text_muted"]),
                (item["time"], 110, palette["text"]),
                (item["status"], 100, palette["success"]),
            ]
            for value, width, color in values:
                ctk.CTkLabel(
                    row,
                    text=value,
                    width=width,
                    font=("SF Pro Text", 12, "bold"),
                    text_color=color,
                    anchor="w",
                ).pack(side="left", padx=6, pady=SPACING["inner"])

    def clear_attendance(self):
        if not self.attendance_manager:
            return
        confirmed = messagebox.askyesno("Clear Attendance", "Delete all attendance records?")
        if not confirmed:
            return
        self.attendance_manager.clear_attendance()
        self.load_attendance_data()


class ReportsPage(ctk.CTkFrame):
    def __init__(self, master, attendance_manager=None, face_manager=None, theme_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        self.attendance_manager = attendance_manager
        self.face_manager = face_manager
        self.theme_manager = theme_manager or ThemeManager()

        self.configure(fg_color=self.theme_manager.get_color("window"))
        self.create_page()

    def create_page(self):
        palette = colors()
        container = ctk.CTkFrame(self, fg_color=palette["window"], corner_radius=0)
        container.pack(fill="both", expand=True, padx=SPACING["outer"], pady=SPACING["outer"])

        ctk.CTkLabel(
            container,
            text="Reports",
            font=("SF Pro Display", 30, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            container,
            text="Daily recognition insights, attendance trend, and system overview.",
            font=("SF Pro Text", 13),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(4, 18))

        self.report_body = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0)
        self.report_body.pack(fill="both", expand=True)

    def on_show(self):
        self.load_summary_report()

    def load_summary_report(self):
        if not self.attendance_manager:
            return

        palette = colors()
        clear_children(self.report_body)

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=13)).strftime("%Y-%m-%d")
        today_records = self.attendance_manager.get_today_attendance()
        records = self.attendance_manager.get_attendance_by_date_range(start_date, end_date)
        face_stats = self.face_manager.get_statistics() if self.face_manager else {}

        cards = ctk.CTkFrame(self.report_body, fg_color="transparent", corner_radius=0)
        cards.pack(fill="x")
        for column in range(4):
            cards.grid_columnconfigure(column, weight=1, uniform="reports")

        present_today = len(today_records)
        total_registered = face_stats.get("known_faces_count", 0)
        recognized_today = face_stats.get("recognized_count", 0)
        unknown_events = face_stats.get("unknown_faces_count", 0)

        MetricCard(cards, "Present Today", present_today, "success").grid(row=0, column=0, sticky="ew", padx=(0, 9))
        MetricCard(cards, "Total Registered", total_registered, "accent").grid(row=0, column=1, sticky="ew", padx=9)
        MetricCard(cards, "Recognized Today", recognized_today, "text").grid(row=0, column=2, sticky="ew", padx=9)
        MetricCard(cards, "Unknown Events", unknown_events, "warning").grid(row=0, column=3, sticky="ew", padx=(9, 0))

        if not records and recognized_today == 0 and unknown_events == 0:
            self.create_report_empty_state()
            return

        charts = ctk.CTkFrame(self.report_body, fg_color="transparent", corner_radius=0)
        charts.pack(fill="both", expand=True, pady=(SPACING["card"], 0))
        charts.grid_columnconfigure(0, weight=3)
        charts.grid_columnconfigure(1, weight=2)
        charts.grid_rowconfigure(0, weight=1)

        trend_card = GlassCard(charts, title="Attendance Trend")
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self.render_trend_chart(trend_card.content, records)

        overview_card = GlassCard(charts, title="Recognition Overview")
        overview_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.render_recognition_overview(overview_card.content, recognized_today, unknown_events)

    def create_report_empty_state(self):
        palette = colors()
        empty = GlassCard(self.report_body)
        empty.pack(fill="both", expand=True, pady=(SPACING["card"], 0))
        inner = ctk.CTkFrame(empty.content, fg_color=palette["accent_soft"], corner_radius=18)
        inner.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            inner,
            text="No report data yet",
            font=("SF Pro Display", 24, "bold"),
            text_color=palette["text"],
        ).pack(pady=(58, 8))
        ctk.CTkLabel(
            inner,
            text="Attendance insights will appear here after recognition begins.",
            font=("SF Pro Text", 14),
            text_color=palette["text_muted"],
            justify="center",
        ).pack(pady=(0, 58))

    def render_trend_chart(self, parent, records):
        palette = colors()
        today = datetime.now()
        days = [(today - timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(13, -1, -1)]
        counts = {day: 0 for day in days}
        for record in records:
            date = record[3]
            if date in counts and record[5] == "Present":
                counts[date] += 1

        max_count = max(max(counts.values()), 1)
        for day in days[-10:]:
            row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
            row.pack(fill="x", pady=5)
            label = datetime.strptime(day, "%Y-%m-%d").strftime("%b %d")
            ctk.CTkLabel(
                row,
                text=label,
                width=62,
                font=("SF Pro Text", 12, "bold"),
                text_color=palette["text_muted"],
                anchor="w",
            ).pack(side="left")

            track = ctk.CTkFrame(row, fg_color=palette["surface_alt"], corner_radius=6, height=10)
            track.pack(side="left", fill="x", expand=True, padx=10)
            track.pack_propagate(False)
            fill_width = max(5, int(260 * (counts[day] / max_count))) if counts[day] else 0
            if fill_width:
                ctk.CTkFrame(track, fg_color=palette["accent"], corner_radius=6, width=fill_width).place(
                    x=0, y=0, relheight=1
                )

            ctk.CTkLabel(
                row,
                text=str(counts[day]),
                width=32,
                font=("SF Pro Text", 12, "bold"),
                text_color=palette["text"],
                anchor="e",
            ).pack(side="right")

    def render_recognition_overview(self, parent, recognized_today, unknown_events):
        palette = colors()
        total_events = recognized_today + unknown_events

        top = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top.pack(fill="x", pady=(4, 18))
        self.overview_value(top, "Known", recognized_today, palette["success"]).pack(side="left", fill="x", expand=True)
        self.overview_value(top, "Unknown", unknown_events, palette["warning"]).pack(
            side="left", fill="x", expand=True, padx=(12, 0)
        )

        progress = ctk.CTkProgressBar(
            parent,
            height=12,
            corner_radius=8,
            fg_color=palette["surface_alt"],
            progress_color=palette["accent"],
        )
        progress.pack(fill="x", pady=(2, 10))
        progress.set((recognized_today / total_events) if total_events else 0)

        ctk.CTkLabel(
            parent,
            text="Known recognition share" if total_events else "Recognition events will appear here",
            font=("SF Pro Text", 12, "bold"),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x")

        if total_events:
            ctk.CTkLabel(
                parent,
                text=f"{recognized_today} known of {total_events} events today",
                font=("SF Pro Display", 22, "bold"),
                text_color=palette["text"],
                anchor="w",
            ).pack(fill="x", pady=(22, 4))
            ctk.CTkLabel(
                parent,
                text="Unknown detections are cooldown-limited to continuous events.",
                font=("SF Pro Text", 12),
                text_color=palette["text_muted"],
                anchor="w",
                wraplength=280,
            ).pack(fill="x")

    def overview_value(self, parent, title, value, accent):
        palette = colors()
        box = ctk.CTkFrame(
            parent,
            fg_color=palette["surface_alt"],
            corner_radius=16,
            border_width=1,
            border_color=palette["border_soft"],
        )
        ctk.CTkLabel(
            box,
            text=str(value),
            font=("SF Pro Display", 28, "bold"),
            text_color=accent,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(
            box,
            text=title,
            font=("SF Pro Text", 12, "bold"),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 12))
        return box


class SettingsPage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        face_manager=None,
        attendance_manager=None,
        on_reset=None,
        theme_manager=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.face_manager = face_manager
        self.attendance_manager = attendance_manager
        self.on_reset = on_reset
        self.theme_manager = theme_manager or ThemeManager()
        self.theme_var = ctk.StringVar(value=self._theme_label())

        self.configure(fg_color=self.theme_manager.get_color("window"))
        self.create_page()

    def create_page(self):
        palette = colors()
        container = ctk.CTkFrame(self, fg_color=palette["window"], corner_radius=0)
        container.pack(fill="both", expand=True, padx=SPACING["outer"], pady=SPACING["outer"])

        ctk.CTkLabel(
            container,
            text="Settings",
            font=("SF Pro Display", 30, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            container,
            text="Appearance, data resets, and app information.",
            font=("SF Pro Text", 13),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(4, 18))

        settings = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0)
        settings.pack(fill="x")

        appearance = GlassCard(settings, title="Appearance")
        appearance.pack(fill="x", pady=(0, SPACING["card"]))
        self.settings_row(
            appearance.content,
            "Interface theme",
            "Choose the visual mode used across the app.",
            lambda row: self.create_theme_control(row),
        )

        data_card = GlassCard(settings, title="Data")
        data_card.pack(fill="x", pady=(0, SPACING["card"]))
        self.settings_row(
            data_card.content,
            "Reset Attendance Data",
            "Clear all attendance records and daily counters.",
            lambda row: GlassButton(
                row,
                text="Reset",
                width=110,
                variant="danger",
                command=self.reset_attendance_data,
            ),
        )
        self.settings_row(
            data_card.content,
            "Reset Face Database",
            "Delete all registered faces and profile photos.",
            lambda row: GlassButton(
                row,
                text="Reset",
                width=110,
                variant="danger",
                command=self.reset_face_database,
            ),
            top_pad=10,
        )

        about = GlassCard(settings, title="About App")
        about.pack(fill="x")
        self.settings_row(
            about.content,
            "Face Attendance Studio",
            "Local face attendance system using DeepFace embeddings and SQLite storage.",
            lambda row: ctk.CTkLabel(
                row,
                text="Portfolio build",
                font=("SF Pro Text", 12, "bold"),
                text_color=palette["accent"],
                fg_color=palette["accent_soft"],
                corner_radius=12,
            ),
        )

    def create_theme_control(self, parent):
        palette = colors()
        control = ctk.CTkSegmentedButton(
            parent,
            values=["Dark", "Light", "System"],
            variable=self.theme_var,
            command=self.set_theme,
            fg_color=palette["surface_alt"],
            selected_color=palette["accent"],
            selected_hover_color=palette["accent_hover"],
            unselected_color=palette["surface_alt"],
            unselected_hover_color=palette["surface_hover"],
            text_color=palette["text"],
            font=("SF Pro Text", 12, "bold"),
            height=34,
            corner_radius=12,
        )
        control.set(self._theme_label())
        return control

    def settings_row(self, parent, title, subtitle, control_factory, top_pad=0):
        palette = colors()
        row = row_frame(parent)
        row.pack(fill="x", pady=(top_pad, 0))

        text = ctk.CTkFrame(row, fg_color="transparent", corner_radius=0)
        text.pack(side="left", fill="x", expand=True, padx=14, pady=13)
        ctk.CTkLabel(
            text,
            text=title,
            font=("SF Pro Text", 14, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            text,
            text=subtitle,
            font=("SF Pro Text", 12),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(3, 0))

        control = control_factory(row)
        control.pack(side="right", padx=14, pady=13)

    def on_show(self):
        self.theme_var.set(self._theme_label())

    def set_theme(self, value):
        theme = {
            "Dark": ThemeManager.DARK,
            "Light": ThemeManager.LIGHT,
            "System": ThemeManager.SYSTEM,
        }.get(value, ThemeManager.DARK)
        self.theme_manager.set_theme(theme)

    def reset_attendance_data(self):
        if not self.attendance_manager:
            return
        confirmed = messagebox.askyesno("Reset Attendance Data", "Delete all attendance records?")
        if not confirmed:
            return
        self.attendance_manager.clear_attendance()
        if self.face_manager:
            self.face_manager.clear_unknown_faces()
            self.face_manager.recognized_today_set.clear()
            self.face_manager.recognized_event_count = 0
        if self.on_reset:
            self.on_reset()

    def reset_face_database(self):
        if not self.face_manager:
            return
        confirmed = messagebox.askyesno("Reset Face Database", "Delete all registered faces?")
        if not confirmed:
            return

        users = list(self.face_manager.database_manager.get_all_users())
        for user in users:
            self.face_manager.delete_registered_face(user[0])
        if self.on_reset:
            self.on_reset()

    def _theme_label(self):
        return {
            ThemeManager.DARK: "Dark",
            ThemeManager.LIGHT: "Light",
            ThemeManager.SYSTEM: "System",
        }.get(self.theme_manager.current_theme, "Dark")
