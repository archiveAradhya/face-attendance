import os
import tkinter as tk

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk

from .theme import ThemeManager


def colors():
    return ThemeManager().get_colors()


SPACING = {
    "outer": 24,
    "card": 18,
    "inner": 18,
}


def _scaled(value, scale):
    return max(1, int(round(value * scale)))


class GlassCard(ctk.CTkFrame):
    def __init__(self, master, title=None, **kwargs):
        palette = colors()
        kwargs.setdefault("fg_color", palette["shadow"])
        kwargs.setdefault("corner_radius", 20)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)

        self.surface = ctk.CTkFrame(
            self,
            fg_color=palette["glass"],
            corner_radius=18,
            border_width=1,
            border_color=palette["border"],
        )
        self.surface.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        self.header = None
        if title:
            self.header = ctk.CTkLabel(
                self.surface,
                text=title,
                font=("SF Pro Display", 16, "bold"),
                text_color=palette["text"],
                anchor="w",
            )
            self.header.pack(fill="x", padx=SPACING["inner"], pady=(SPACING["inner"], 6))

        self.content = ctk.CTkFrame(self.surface, fg_color="transparent", corner_radius=0)
        self.content.pack(
            fill="both",
            expand=True,
            padx=SPACING["inner"],
            pady=(8 if title else SPACING["inner"], SPACING["inner"]),
        )
        self.after(20, self.animate_in)

    def set_title(self, title):
        palette = colors()
        if self.header is None:
            self.header = ctk.CTkLabel(
                self.surface,
                text=title,
                font=("SF Pro Display", 16, "bold"),
                text_color=palette["text"],
                anchor="w",
            )
            self.header.pack(fill="x", padx=SPACING["inner"], pady=(SPACING["inner"], 6), before=self.content)
        else:
            self.header.configure(text=title)

    def animate_in(self, step=0):
        if not self.winfo_exists():
            return
        palette = colors()
        sequence = [palette["shadow"], palette["border_soft"], palette["border"]]
        if step < len(sequence):
            self.surface.configure(border_color=sequence[step])
            self.after(35, lambda: self.animate_in(step + 1))


class GlassButton(ctk.CTkButton):
    def __init__(self, master, variant="primary", **kwargs):
        palette = colors()
        styles = {
            "primary": (palette["accent"], palette["accent_hover"], "#FFFFFF"),
            "secondary": (palette["surface_alt"], palette["surface_hover"], palette["text"]),
            "danger": (palette["danger"], "#FF6961", "#FFFFFF"),
            "success": (palette["success"], "#46E174", "#07110A"),
            "ghost": ("transparent", palette["surface_hover"], palette["text"]),
        }
        fg_color, hover_color, text_color = styles.get(variant, styles["primary"])
        kwargs.setdefault("fg_color", fg_color)
        kwargs.setdefault("hover_color", hover_color)
        kwargs.setdefault("text_color", text_color)
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("height", 38)
        kwargs.setdefault("font", ("SF Pro Text", 13, "bold"))
        kwargs.setdefault("border_width", 1 if variant in ("secondary", "ghost") else 0)
        kwargs.setdefault("border_color", palette["border_soft"])
        super().__init__(master, **kwargs)
        self._base_width = int(kwargs.get("width", self.cget("width") or 100))
        self._base_height = int(kwargs.get("height", self.cget("height") or 38))
        self._animating = False
        self.bind("<Enter>", lambda _event: self._animate_scale(1.05))
        self.bind("<Leave>", lambda _event: self._animate_scale(1.0))

    def _animate_scale(self, target_scale, step=0):
        if not self.winfo_exists():
            return
        steps = 4
        current_width = int(self.cget("width"))
        current_height = int(self.cget("height"))
        target_width = _scaled(self._base_width, target_scale)
        target_height = _scaled(self._base_height, target_scale)
        if step >= steps:
            self.configure(width=target_width, height=target_height)
            return
        next_width = current_width + int((target_width - current_width) / max(1, steps - step))
        next_height = current_height + int((target_height - current_height) / max(1, steps - step))
        self.configure(width=max(1, next_width), height=max(1, next_height))
        self.after(18, lambda: self._animate_scale(target_scale, step + 1))


class GlassEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        palette = colors()
        kwargs.setdefault("fg_color", palette["input"])
        kwargs.setdefault("border_color", palette["border"])
        kwargs.setdefault("text_color", palette["text"])
        kwargs.setdefault("placeholder_text_color", palette["text_dim"])
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("height", 40)
        kwargs.setdefault("font", ("SF Pro Text", 13))
        super().__init__(master, **kwargs)


class GlassLabel(ctk.CTkLabel):
    def __init__(self, master, muted=False, **kwargs):
        palette = colors()
        kwargs.setdefault("text_color", palette["text_muted"] if muted else palette["text"])
        kwargs.setdefault("font", ("SF Pro Text", 13))
        super().__init__(master, **kwargs)


class GlassImage(ctk.CTkLabel):
    def __init__(self, master, image_path=None, size=(96, 96), **kwargs):
        palette = colors()
        kwargs.setdefault("text", "")
        kwargs.setdefault("fg_color", palette["surface_alt"])
        kwargs.setdefault("corner_radius", 12)
        super().__init__(master, **kwargs)

        self.image_size = size
        self._image_ref = None
        self.current_image = None
        if image_path and os.path.exists(image_path):
            self.set_image(image_path)

    def set_image(self, image_path):
        image = Image.open(image_path).convert("RGB")
        image.thumbnail(self.image_size, Image.Resampling.LANCZOS)
        self.current_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        self._image_ref = self.current_image
        self.configure(image=self.current_image, text="")


class CameraView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        palette = colors()
        kwargs.setdefault("fg_color", "#05070B")
        kwargs.setdefault("corner_radius", 18)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", palette["border"])
        super().__init__(master, **kwargs)

        self._image_ref = None
        self.current_image = None
        self._image_history = []
        self.preview = tk.Label(
            self,
            text="Camera is Off\nClick Start Camera to begin live recognition",
            foreground=palette["text_muted"],
            font=("SF Pro Display", 18, "bold"),
            justify="center",
            background="#05070B",
            borderwidth=0,
            highlightthickness=0,
        )
        self.preview.pack(fill="both", expand=True, padx=SPACING["inner"], pady=SPACING["inner"])
        self._has_frame = False

    def set_active(self, active):
        palette = colors()
        self.configure(border_color=palette["glow"] if active else palette["border"])

    def show_placeholder(self, message=None):
        if not self.winfo_exists() or not self.preview.winfo_exists():
            return
        palette = colors()
        self.preview.configure(
            image="",
            text=message or "Camera is Off\nClick Start Camera to begin live recognition",
            foreground=palette["text_muted"],
            background="#05070B",
        )
        self._has_frame = False

    def update_frame(self, frame):
        if not self.winfo_exists() or not self.preview.winfo_exists():
            return
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            container_width = max(self.winfo_width() - 32, 320)
            container_height = max(self.winfo_height() - 32, 240)
            image = Image.fromarray(frame_rgb)
            image.thumbnail((container_width, container_height), Image.Resampling.LANCZOS)
            if self.current_image is not None:
                self._image_history.append(self.current_image)
                self._image_history = self._image_history[-8:]
            self.current_image = ImageTk.PhotoImage(image=image)
            self._image_ref = self.current_image
            self.preview.configure(image=self.current_image, text="")
            self._has_frame = True
        except Exception as exc:
            self.show_placeholder(f"Camera preview unavailable\n{exc}")


class StatusBadge(ctk.CTkLabel):
    def __init__(self, master, status="offline", **kwargs):
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("width", 88)
        kwargs.setdefault("height", 28)
        super().__init__(master, **kwargs)
        self.set_status(status)

    def set_status(self, status):
        palette = colors()
        styles = {
            "online": ("Live", palette["success"], palette["success_soft"]),
            "checking": ("Checking", palette["warning"], palette["warning_soft"]),
            "offline": ("Offline", palette["text_muted"], palette["surface_alt"]),
            "error": ("Error", palette["danger"], palette["danger_soft"]),
        }
        label, text_color, fg_color = styles.get(status, styles["offline"])
        self.configure(
            text=label,
            text_color=text_color,
            fg_color=fg_color,
            font=("SF Pro Text", 12, "bold"),
        )


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title, value="0", accent="accent", **kwargs):
        palette = colors()
        kwargs.setdefault("fg_color", palette["glass"])
        kwargs.setdefault("corner_radius", 18)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", palette["border"])
        super().__init__(master, **kwargs)

        self.accent_key = accent
        self.value_label = ctk.CTkLabel(
            self,
            text=str(value),
            font=("SF Pro Display", 30, "bold"),
            text_color=palette.get(accent, palette["accent"]),
            anchor="w",
        )
        self.value_label.pack(fill="x", padx=SPACING["inner"], pady=(SPACING["inner"], 0))

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=("SF Pro Text", 13, "bold"),
            text_color=palette["text_muted"],
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=SPACING["inner"], pady=(2, SPACING["inner"]))

    def set_value(self, value):
        self.value_label.configure(text=str(value))


class GlassListbox(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        palette = colors()
        kwargs.setdefault("fg_color", palette["glass_subtle"])
        kwargs.setdefault("corner_radius", 16)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", palette["border_soft"])
        kwargs.setdefault("scrollbar_button_color", palette["surface_hover"])
        kwargs.setdefault("scrollbar_fg_color", palette["surface"])
        super().__init__(master, **kwargs)
        self.items = []

    def clear_items(self):
        for item in self.items:
            item.destroy()
        self.items = []


def row_frame(master):
    palette = colors()
    return ctk.CTkFrame(
        master,
        fg_color=palette["surface_alt"],
        corner_radius=14,
        border_width=1,
        border_color=palette["border_soft"],
    )
