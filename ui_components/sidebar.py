import customtkinter as ctk

from .theme import ThemeManager


class SidebarNavigation(ctk.CTkFrame):
    def __init__(self, master, callback=None, theme_manager=None, **kwargs):
        self.theme_manager = theme_manager or ThemeManager()
        self.callback = callback
        self.current_page = "home"
        self.buttons = {}

        palette = self.theme_manager.get_colors()
        kwargs.setdefault("width", 270)
        kwargs.setdefault("fg_color", palette["sidebar"])
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)

        self.pack_propagate(False)
        self.create_sidebar()
        self.theme_manager.add_listener(self.on_theme_change)

    def create_sidebar(self):
        palette = self.theme_manager.get_colors()

        brand = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        brand.pack(fill="x", padx=20, pady=(28, 26))

        ctk.CTkLabel(
            brand,
            text="Face ID",
            font=("SF Pro Display", 28, "bold"),
            text_color=palette["text"],
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            brand,
            text="Attendance Studio",
            font=("SF Pro Text", 13, "bold"),
            text_color=palette["text_muted"],
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        menu = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        menu.pack(fill="both", expand=True, padx=16)

        self.nav_items = [
            ("home", "Home", "⌘ "),
            ("live", "Live Attendance", "◉ "),
            ("attendance", "Attendance Records", "▤ "),
            ("faces", "Face Database", "◇ "),
            ("reports", "Reports", "▥ "),
            ("settings", "Settings", "⚙ "),
        ]

        for page, label, icon in self.nav_items:
            self.buttons[page] = self.create_nav_button(menu, page, label, icon)

        bottom = ctk.CTkFrame(
            self,
            fg_color=palette["glass_subtle"],
            corner_radius=18,
            border_width=1,
            border_color=palette["border_soft"],
        )
        bottom.pack(fill="x", padx=20, pady=(18, 20))

        self.theme_switch = ctk.CTkSwitch(
            bottom,
            text="Dark Mode",
            font=("SF Pro Text", 13, "bold"),
            text_color=palette["text"],
            progress_color=palette["accent"],
            button_color="#FFFFFF",
            fg_color=palette["surface_hover"],
            command=self.toggle_theme,
        )
        self.theme_switch.pack(fill="x", padx=14, pady=14)
        self.theme_switch.select() if self.theme_manager.current_theme == ThemeManager.DARK else self.theme_switch.deselect()

        self.set_active_page(self.current_page)

    def create_nav_button(self, parent, page, label, icon):
        palette = self.theme_manager.get_colors()
        button = ctk.CTkButton(
            parent,
            text=f"{icon}  {label}",
            height=46,
            anchor="w",
            corner_radius=14,
            font=("SF Pro Text", 14, "bold"),
            text_color=palette["text_muted"],
            fg_color="transparent",
            hover_color=palette["surface_hover"],
            command=lambda: self.navigate_to(page),
        )
        button.pack(fill="x", pady=6)
        button.bind("<Enter>", lambda _event: self.animate_hover(page, True))
        button.bind("<Leave>", lambda _event: self.animate_hover(page, False))
        return button

    def animate_hover(self, page, entering, step=0):
        if page == self.current_page or page not in self.buttons:
            return
        palette = self.theme_manager.get_colors()
        colors = [palette["surface"], palette["surface_alt"], palette["surface_hover"]]
        if not entering:
            colors = list(reversed(colors))
        index = min(step, len(colors) - 1)
        self.buttons[page].configure(
            fg_color=colors[index] if entering or step < len(colors) - 1 else "transparent",
            text_color=palette["text"] if entering else palette["text_muted"],
        )
        if step < len(colors) - 1:
            self.after(18, lambda: self.animate_hover(page, entering, step + 1))

    def navigate_to(self, page):
        if page == self.current_page:
            return
        self.set_active_page(page)
        if self.callback:
            self.callback(page)

    def set_active_page(self, page):
        self.current_page = page
        palette = self.theme_manager.get_colors()
        for item_page, button in self.buttons.items():
            active = item_page == page
            button.configure(
                fg_color=palette["sidebar_active"] if active else "transparent",
                text_color=palette["text"] if active else palette["text_muted"],
                hover_color=palette["sidebar_active"] if active else palette["surface_hover"],
                border_width=1 if active else 0,
                border_color=palette["glow"] if active else palette["sidebar"],
            )

    def toggle_theme(self):
        selected = self.theme_switch.get() == 1
        self.theme_manager.set_theme(ThemeManager.DARK if selected else ThemeManager.LIGHT)

    def on_theme_change(self, theme, palette):
        self.configure(fg_color=palette["sidebar"])
        if hasattr(self, "theme_switch"):
            self.theme_switch.configure(
                text_color=palette["text"],
                progress_color=palette["accent"],
                fg_color=palette["surface_hover"],
            )
            self.theme_switch.select() if self.theme_manager._resolved_theme() == ThemeManager.DARK else self.theme_switch.deselect()
        self.set_active_page(self.current_page)

    def get_current_page(self):
        return self.current_page
