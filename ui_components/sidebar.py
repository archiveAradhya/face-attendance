import customtkinter as ctk
from .theme import ThemeManager
from .widgets import GlassCard, GlassButton, inject_glass_effect

class SidebarNavigation(ctk.CTkFrame):
    def __init__(self, master, callback=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.callback = callback
        self.current_page = "home"
        self.theme_manager = ThemeManager()
        
        # Configure sidebar
        self.configure(
            width=250,
            fg_color=self.theme_manager.get_color("sidebar_bg"),
            corner_radius=0,
            border_width=0
        )
        
        self.create_sidebar()
        
        # Listen for theme changes
        self.theme_manager.add_listener(self.on_theme_change)
    
    def create_sidebar(self):
        # Logo section
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        logo_frame.pack(fill="x", padx=20, pady=(20, 30))
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="👤\nFace Attendance",
            font=("SF Pro Display", 24, "bold"),
            text_color=("white", "black"),
            justify="center"
        )
        logo_label.pack()
        
        # Navigation menu
        menu_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        menu_frame.pack(fill="both", expand=True, padx=10)
        
        # Menu items
        menu_items = [
            {
                "icon": "🏠",
                "text": "Home",
                "page": "home",
                "action": lambda: self.navigate_to("home")
            },
            {
                "icon": "📹",
                "text": "Live Attendance",
                "page": "live",
                "action": lambda: self.navigate_to("live")
            },
            {
                "icon": "📋",
                "text": "Attendance Records",
                "page": "attendance",
                "action": lambda: self.navigate_to("attendance")
            },
            {
                "icon": "👥",
                "text": "Face Database",
                "page": "faces",
                "action": lambda: self.navigate_to("faces")
            },
            {
                "icon": "📊",
                "text": "Reports",
                "page": "reports",
                "action": lambda: self.navigate_to("reports")
            },
            {
                "icon": "⚙️",
                "text": "Settings",
                "page": "settings",
                "action": lambda: self.navigate_to("settings")
            }
        ]
        
        self.menu_buttons = []
        for item in menu_items:
            button = self.create_menu_button(
                icon=item["icon"],
                text=item["text"],
                page=item["page"],
                action=item["action"]
            )
            self.menu_buttons.append(button)
        
        # Bottom section
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        bottom_frame.pack(fill="x", padx=20, pady=(20, 20))
        
        # Profile button
        profile_button = ctk.CTkButton(
            bottom_frame,
            text="👤 Admin Profile",
            font=("SF Pro Text", 12),
            text_color=("white", "black"),
            fg_color="rgba(255, 255, 255, 0.1)",
            hover_color="rgba(255, 255, 255, 0.2)",
            corner_radius=10,
            command=self.show_profile
        )
        profile_button.pack(fill="x", pady=5)
        
        # Theme toggle
        theme_button = ctk.CTkButton(
            bottom_frame,
            text="🌙" if self.theme_manager.current_theme == "dark" else "☀️",
            font=("SF Pro Text", 14),
            text_color=("white", "black"),
            fg_color="rgba(255, 255, 255, 0.1)",
            hover_color="rgba(255, 255, 255, 0.2)",
            corner_radius=10,
            width=40,
            command=self.toggle_theme
        )
        theme_button.pack(pady=5)
    
    def create_menu_button(self, icon, text, page, action):
        button_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        button_frame.pack(fill="x", padx=10, pady=2)
        
        button = ctk.CTkButton(
            button_frame,
            text=f"{icon}  {text}",
            font=("SF Pro Text", 13, "semibold" if page == self.current_page else "normal"),
            text_color=("white", "black"),
            fg_color="rgba(0, 132, 255, 0.3)" if page == self.current_page else "rgba(255, 255, 255, 0.1)",
            hover_color="rgba(255, 255, 255, 0.2)",
            anchor="w",
            corner_radius=10,
            height=40,
            command=lambda: self.select_button(button, page, action)
        )
        button.pack(fill="x", pady=2)
        
        return button
    
    def select_button(self, button, page, action):
        # Update current page
        self.current_page = page
        
        # Update all buttons
        for btn in self.menu_buttons:
            if btn == button:
                btn.configure(
                    font=("SF Pro Text", 13, "semibold"),
                    fg_color="rgba(0, 132, 255, 0.3)"
                )
            else:
                btn.configure(
                    font=("SF Pro Text", 13, "normal"),
                    fg_color="rgba(255, 255, 255, 0.1)"
                )
        
        # Execute action
        if action:
            action()
    
    def navigate_to(self, page):
        if self.callback:
            self.callback(page)
    
    def show_profile(self):
        # Placeholder for profile action
        print("Show admin profile")
        if self.callback:
            self.callback("profile")
    
    def toggle_theme(self):
        self.theme_manager.toggle_theme()
    
    def on_theme_change(self, theme, colors):
        # Update theme icons
        # This would need to be implemented to update button icons
        pass
    
    def set_active_page(self, page):
        self.current_page = page
        # Update button states
        for i, button in enumerate(self.menu_buttons):
            page_name = ["home", "live", "attendance", "faces", "reports", "settings"][i]
            if page_name == page:
                self.select_button(button, page_name, lambda: self.navigate_to(page_name))
                break
    
    def get_current_page(self):
        return self.current_page