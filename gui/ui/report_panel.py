from gui.ui.theme import Colors, Fonts
import tkinter as tk

class ReportPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Colors.PANEL_BG, **kwargs)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        
        self.lbl_stitch_count = self._create_metric("CHAIN COUNT", "0", 0)
        self.lbl_direction = self._create_metric("DIRECTION", "--", 1)
        self.lbl_yarn_width = self._create_metric("YARN WIDTH", "0px", 2)

    def _create_metric(self, title, default_val, col_index):
        frame = tk.Frame(self, bg=Colors.PANEL_BG, pady=10)
        frame.grid(row=0, column=col_index, sticky="nsew")
        
        tk.Label(frame, text=title, bg=Colors.PANEL_BG, fg=Colors.TEXT_DIM, 
                 font=("Helvetica Neue", 10, "bold")).pack(side=tk.TOP)
        
        val_label = tk.Label(frame, text=default_val, bg=Colors.PANEL_BG, fg=Colors.ACCENT, 
                             font=("Helvetica Neue", 18, "bold"))
        val_label.pack(side=tk.TOP, pady=5)
        
        return val_label

    def update_report(self, stitch_count, direction_text, width_px):
        self.lbl_stitch_count.config(text=str(stitch_count))
        self.lbl_direction.config(text=direction_text)
        self.lbl_yarn_width.config(text=f"{width_px:.1f}px")

    def reset_report(self):
        self.lbl_stitch_count.config(text="0")
        self.lbl_direction.config(text="--")
        self.lbl_yarn_width.config(text="0px")
