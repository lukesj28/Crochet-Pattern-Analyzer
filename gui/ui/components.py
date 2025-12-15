import tkinter as tk
from gui.ui.theme import Colors, Fonts

class ModernButton(tk.Label):
    def __init__(self, parent, text, command, primary=True, **kwargs):
        self.command = command
        self.is_primary = primary
        self.is_disabled = False
        
        self.bg_color = Colors.ACCENT if primary else Colors.PANEL_BG
        self.fg_color = Colors.TEXT_BRIGHT if primary else Colors.TEXT_MAIN
        self.hover_color = Colors.ACCENT_HOVER if primary else "#3E3E42"
        
        super().__init__(
            parent,
            text=text,
            bg=self.bg_color,
            fg=self.fg_color,
            font=Fonts.BUTTON,
            padx=20,

            **kwargs
        )
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        if not self.is_disabled:
            self.config(bg=self.hover_color)

    def _on_leave(self, event):
        if not self.is_disabled:
            self.config(bg=self.bg_color)

    def _on_click(self, event):
        if not self.is_disabled and self.command:
            self.command()

    def set_text(self, text):
        self.config(text=text)

    def set_disabled(self, disabled):
        self.is_disabled = disabled
        if disabled:
            self.config(bg=Colors.BORDER, fg=Colors.TEXT_DIM)
        else:
            self.config(bg=self.bg_color, fg=self.fg_color)

class StatusLabel(tk.Label):
    def __init__(self, parent, text="Ready", **kwargs):
        super().__init__(
            parent,
            text=text,
            bg=Colors.PANEL_BG,
            fg=Colors.TEXT_DIM,
            font=Fonts.STATUS,
            anchor="w",
            **kwargs
        )
        
    def set_status(self, text, type="normal"):
        color = Colors.TEXT_MAIN
        if type == "success": color = Colors.SUCCESS
        elif type == "error": color = Colors.ERROR
        elif type == "warning": color = Colors.WARNING
        
        self.config(text=text, fg=color)
