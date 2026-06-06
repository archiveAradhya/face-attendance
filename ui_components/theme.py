import customtkinter as ctk

class ThemeManager:
    DARK = "dark"
    LIGHT = "light"
    
    DARK_COLORS = {
        "bg_primary": "#000000",
        "bg_secondary": "#1C1C1E",
        "bg_card": "rgba(28, 28, 30, 0.8)",
        "bg_card_hex": "#1C1C1E",
        "bg_input": "#2C2C2E",
        "text_primary": "#FFFFFF",
        "text_secondary": "#8E8E93",
        "accent": "#0A84FF",
        "accent_hover": "#409CFF",
        "success": "#30D158",
        "danger": "#FF453A",
        "warning": "#FF9F0A",
        "border": "rgba(255, 255, 255, 0.1)",
        "border_hex": "#38383A",
        "sidebar_bg": "rgba(20, 20, 22, 0.9)",
        "sidebar_bg_hex": "#141416",
        "hover": "rgba(255, 255, 255, 0.05)",
        "hover_hex": "#1C1C1E",
        "shadow": "rgba(0, 0, 0, 0.5)"
    }
    
    LIGHT_COLORS = {
        "bg_primary": "#F2F2F7",
        "bg_secondary": "#FFFFFF",
        "bg_card": "rgba(255, 255, 255, 0.8)",
        "bg_card_hex": "#FFFFFF",
        "bg_input": "#F2F2F7",
        "text_primary": "#000000",
        "text_secondary": "#3C3C43",
        "accent": "#007AFF",
        "accent_hover": "#0051D5",
        "success": "#34C759",
        "danger": "#FF3B30",
        "warning": "#FF9500",
        "border": "rgba(0, 0, 0, 0.1)",
        "border_hex": "#D1D1D6",
        "sidebar_bg": "rgba(242, 242, 247, 0.9)",
        "sidebar_bg_hex": "#E5E5EA",
        "hover": "rgba(0, 0, 0, 0.03)",
        "hover_hex": "#F2F2F7",
        "shadow": "rgba(0, 0, 0, 0.1)"
    }
    
    def __init__(self):
        self.current_theme = self.DARK
        self.colors = self.DARK_COLORS.copy()
        self.listeners = []
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
    
    def toggle_theme(self):
        if self.current_theme == self.DARK:
            self.set_theme(self.LIGHT)
        else:
            self.set_theme(self.DARK)
    
    def set_theme(self, theme):
        self.current_theme = theme
        if theme == self.DARK:
            self.colors = self.DARK_COLORS.copy()
            ctk.set_appearance_mode("dark")
        else:
            self.colors = self.LIGHT_COLORS.copy()
            ctk.set_appearance_mode("light")
        
        for listener in self.listeners:
            listener(self.current_theme, self.colors)
    
    def add_listener(self, callback):
        self.listeners.append(callback)
    
    def remove_listener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def get_color(self, key):
        return self.colors.get(key, "")
    
    def get_colors(self):
        return self.colors.copy()