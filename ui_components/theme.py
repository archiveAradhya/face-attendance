import customtkinter as ctk


class ThemeManager:
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"

    DARK_COLORS = {
        "window": "#05070B",
        "window_alt": "#0A0D14",
        "sidebar": "#090B10",
        "sidebar_active": "#112845",
        "surface": "#10141C",
        "surface_alt": "#171C26",
        "surface_hover": "#202938",
        "glass": "#121722",
        "glass_light": "#1A2130",
        "glass_subtle": "#0D111A",
        "border": "#263142",
        "border_soft": "#1D2633",
        "text": "#F5F5F7",
        "text_muted": "#AAB4C2",
        "text_dim": "#778294",
        "accent": "#0A84FF",
        "accent_hover": "#4CB3FF",
        "accent_soft": "#102B49",
        "success": "#30D158",
        "success_soft": "#102B21",
        "danger": "#FF453A",
        "danger_soft": "#3A1519",
        "warning": "#FFD60A",
        "warning_soft": "#3A3213",
        "input": "#111722",
        "shadow": "#050506",
        "glow": "#2F7DCE",
    }

    LIGHT_COLORS = {
        "window": "#F6F8FB",
        "window_alt": "#EEF3F8",
        "sidebar": "#EEF3F8",
        "sidebar_active": "#DCEBFF",
        "surface": "#FFFFFF",
        "surface_alt": "#F5F8FC",
        "surface_hover": "#E7EEF7",
        "glass": "#FFFFFF",
        "glass_light": "#FBFCFE",
        "glass_subtle": "#F1F5FA",
        "border": "#D8E0EA",
        "border_soft": "#E5ECF4",
        "text": "#111827",
        "text_muted": "#4B5563",
        "text_dim": "#7A8594",
        "accent": "#007AFF",
        "accent_hover": "#005FCC",
        "accent_soft": "#E3F0FF",
        "success": "#248A3D",
        "success_soft": "#E4F6EA",
        "danger": "#D70015",
        "danger_soft": "#FFE6E8",
        "warning": "#B78103",
        "warning_soft": "#FFF4CF",
        "input": "#FFFFFF",
        "shadow": "#DDE5EF",
        "glow": "#B8D8FF",
    }

    _current_theme = DARK
    _listeners = []

    def __init__(self):
        ctk.set_default_color_theme("blue")
        self._apply_appearance_mode(self._current_theme)

    @property
    def current_theme(self):
        return type(self)._current_theme

    @property
    def colors(self):
        return self.get_colors()

    def toggle_theme(self):
        self.set_theme(self.LIGHT if self.current_theme == self.DARK else self.DARK)

    def set_theme(self, theme):
        if theme not in (self.DARK, self.LIGHT, self.SYSTEM):
            theme = self.DARK

        type(self)._current_theme = theme
        self._apply_appearance_mode(theme)

        colors = self.get_colors()
        for listener in list(type(self)._listeners):
            listener(theme, colors)

    def add_listener(self, callback):
        if callback not in type(self)._listeners:
            type(self)._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in type(self)._listeners:
            type(self)._listeners.remove(callback)

    def get_color(self, key):
        return self.get_colors().get(key, "")

    def get_colors(self):
        source = self.DARK_COLORS if self._resolved_theme() == self.DARK else self.LIGHT_COLORS
        return source.copy()

    def _resolved_theme(self):
        if self.current_theme == self.SYSTEM:
            return self.DARK if ctk.get_appearance_mode() == "Dark" else self.LIGHT
        return self.current_theme

    @staticmethod
    def _apply_appearance_mode(theme):
        mode = {
            ThemeManager.DARK: "Dark",
            ThemeManager.LIGHT: "Light",
            ThemeManager.SYSTEM: "System",
        }.get(theme, "Dark")
        ctk.set_appearance_mode(mode)
