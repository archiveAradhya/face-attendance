import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import os

class GlassCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configure glassmorphism effect
        self.configure(
            fg_color="transparent",
            corner_radius=20,
            border_width=0
        )
        
        # Create glass effect container
        self.glass_frame = ctk.CTkFrame(
            self,
            fg_color="rgba(255, 255, 255, 0.1)",
            corner_radius=15,
            border_width=1,
            border_color="rgba(255, 255, 255, 0.2)"
        )
        self.glass_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title label
        self.title_label = ctk.CTkLabel(
            self.glass_frame,
            font=("SF Pro Display", 16, "bold"),
            text_color=("white", "black")
        )
        self.title_label.pack(pady=(15, 10))
        
        # Content frame
        self.content_frame = ctk.CTkFrame(
            self.glass_frame,
            fg_color="transparent",
            corner_radius=0,
            border_width=0
        )
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def set_title(self, title):
        self.title_label.configure(text=title)

class GlassButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configure glassmorphism button
        self.configure(
            corner_radius=12,
            font=("SF Pro Display", 12, "semibold"),
            text_color=("white", "black"),
            anchor="center"
        )

class GlassEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configure glassmorphism entry
        self.configure(
            corner_radius=12,
            font=("SF Pro Text", 12),
            text_color=("white", "black"),
            placeholder_text_color=("gray60", "gray40")
        )

class GlassFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configure glass effect
        self.configure(
            fg_color="rgba(255, 255, 255, 0.05)",
            corner_radius=15,
            border_width=1,
            border_color="rgba(255, 255, 255, 0.1)"
        )

class GlassLabel(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configure glass label
        font = kwargs.pop("font", ("SF Pro Text", 12))
        text_color = kwargs.pop("text_color", ("white", "black"))
        
        self.configure(
            font=font,
            text_color=text_color
        )

class GlassImage(ctk.CTkLabel):
    def __init__(self, master, image_path=None, size=(100, 100), **kwargs):
        super().__init__(master, **kwargs)
        
        self.image_size = size
        self.pil_image = None
        self.photo_image = None
        
        if image_path and os.path.exists(image_path):
            self.load_image(image_path)
    
    def load_image(self, image_path):
        try:
            # Load and resize image
            self.pil_image = Image.open(image_path)
            self.pil_image = self.pil_image.resize(self.image_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(self.pil_image)
            
            # Configure label
            self.configure(image=self.photo_image)
            
        except Exception as e:
            print(f"Error loading image: {e}")
    
    def set_image(self, image_path):
        self.load_image(image_path)

class CameraView(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(
            fg_color="rgba(0, 0, 0, 0.3)",
            corner_radius=15,
            border_width=2,
            border_color="rgba(255, 255, 255, 0.2)",
            text="Camera Feed",
            font=("SF Pro Text", 14)
        )
        
        self.camera_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=12,
            border_width=0
        )
        self.camera_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def update_frame(self, frame):
        try:
            # Convert OpenCV frame to PhotoImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (640, 480))
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_resized)
            photo_image = ImageTk.PhotoImage(pil_image)
            
            # Update label
            self.camera_frame.configure(image=photo_image)
            self.camera_frame.image = photo_image  # Keep reference
            
        except Exception as e:
            print(f"Error updating camera frame: {e}")

class StatusBadge(ctk.CTkLabel):
    def __init__(self, master, status="active", **kwargs):
        super().__init__(master, **kwargs)
        
        self.status = status
        self.update_style()
    
    def set_status(self, status):
        self.status = status
        self.update_style()
    
    def update_style(self):
        if self.status == "active":
            self.configure(
                text="● Active",
                text_color=("#30D158", "#30D158"),
                font=("SF Pro Text", 10, "bold")
            )
        elif self.status == "inactive":
            self.configure(
                text="● Inactive",
                text_color=("#8E8E93", "#8E8E93"),
                font=("SF Pro Text", 10, "bold")
            )
        elif self.status == "warning":
            self.configure(
                text="● Warning",
                text_color=("#FF9F0A", "#FF9F0A"),
                font=("SF Pro Text", 10, "bold")
            )
        elif self.status == "error":
            self.configure(
                text="● Error",
                text_color=("#FF453A", "#FF453A"),
                font=("SF Pro Text", 10, "bold")
            )

class ProgressRing(ctk.CTkCanvas):
    def __init__(self, master, size=100, **kwargs):
        super().__init__(master, **kwargs)
        
        self.size = size
        self.configure(width=size, height=size, highlightthickness=0)
        
        # Create ring
        self.ring = self.create_oval(
            5, 5, size-5, size-5,
            outline="rgba(255, 255, 255, 0.2)",
            width=3,
            style="arc"
        )
        
        # Create text
        self.text = self.create_text(
            size//2, size//2,
            text="0%",
            font=("SF Pro Display", 12, "bold"),
            fill="white"
        )
    
    def set_progress(self, percentage):
        # Calculate angle for arc (0% = 0°, 100% = 360°)
        angle = (percentage / 100) * 360
        
        # Update ring
        self.itemconfig(self.ring, 
                       extent=angle,
                       outline="rgba(0, 132, 255, 0.8)" if percentage > 0 else "rgba(255, 255, 255, 0.2)")
        
        # Update text
        self.itemconfig(self.text, text=f"{percentage:.0f}%")

class GlassListbox(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configure glass effect
        self.configure(
            fg_color="rgba(255, 255, 255, 0.05)",
            corner_radius=15,
            border_width=1,
            border_color="rgba(255, 255, 255, 0.1)"
        )
        
        self.items = []
        self.selected_index = None
        
        # Configure scrollbar
        self.configure(scrollbar_button_color="rgba(255, 255, 255, 0.3)")
        self.configure(scrollbar_fg_color="rgba(255, 255, 255, 0.5)")
    
    def add_item(self, text, callback=None):
        item_frame = ctk.CTkFrame(
            self,
            fg_color="rgba(255, 255, 255, 0.1)",
            corner_radius=8,
            border_width=0
        )
        item_frame.pack(fill="x", padx=5, pady=2)
        
        item_label = ctk.CTkLabel(
            item_frame,
            text=text,
            font=("SF Pro Text", 12),
            text_color=("white", "black"),
            anchor="w"
        )
        item_label.pack(side="left", padx=10, pady=8)
        
        # Bind click event
        if callback:
            item_frame.bind("<Button-1>", lambda e: callback(text))
            item_label.bind("<Button-1>", lambda e: callback(text))
        
        self.items.append({
            'frame': item_frame,
            'label': item_label,
            'text': text,
            'callback': callback
        })
    
    def clear_items(self):
        for item in self.items:
            item['frame'].destroy()
        self.items = []
        self.selected_index = None
    
    def select_item(self, index):
        if 0 <= index < len(self.items):
            # Deselect previous
            if self.selected_index is not None:
                self.items[self.selected_index]['frame'].configure(fg_color="rgba(255, 255, 255, 0.1)")
            
            # Select new
            self.selected_index = index
            self.items[index]['frame'].configure(fg_color="rgba(0, 132, 255, 0.2)")

def inject_glass_effect(widget, **style):
    """Apply glassmorphism effect to any widget"""
    widget.configure(
        corner_radius=style.get('corner_radius', 12),
        border_width=style.get('border_width', 1),
        border_color=style.get('border_color', "rgba(255, 255, 255, 0.2)"),
        fg_color=style.get('fg_color', "rgba(255, 255, 255, 0.1)")
    )
    return widget