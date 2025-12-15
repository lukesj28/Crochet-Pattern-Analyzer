from gui.ui.theme import Colors, Fonts
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from gui.ui.components import ModernButton

class PipelineViewer(tk.Toplevel):
    def __init__(self, parent, debug_frames):
        super().__init__(parent)
        self.title("Analysis Pipeline Inspection")
        self.geometry("1100x850") 
        self.configure(bg=Colors.BACKGROUND)
        
        self.debug_frames = debug_frames 
        self.current_step = 0
        self.tk_img = None
        
        self._setup_ui()
        
        self.after(100, lambda: self._show_step(0))
        
        self.content_frame.bind("<Configure>", self._on_resize)
        
    def _setup_ui(self):
        self.header_frame = tk.Frame(self, bg=Colors.PANEL_BG, height=60)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.header_frame.pack_propagate(False)
        
        self.lbl_title = tk.Label(self.header_frame, text="Step 0: ...", 
                                  bg=Colors.PANEL_BG, fg=Colors.TEXT_BRIGHT, font=Fonts.HEADER)
        self.lbl_title.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.lbl_desc = tk.Label(self.header_frame, text="...", 
                                 bg=Colors.PANEL_BG, fg=Colors.TEXT_DIM, font=Fonts.MAIN)
        self.lbl_desc.pack(side=tk.LEFT, padx=10, pady=12)

        self.content_frame = tk.Frame(self, bg=Colors.CANVAS_BG)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.content_frame.pack_propagate(False)
        
        self.image_label = tk.Label(self.content_frame, bg=Colors.CANVAS_BG)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        self.footer = tk.Frame(self, bg=Colors.BACKGROUND, height=80)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X)
        self.footer.pack_propagate(False)
        
        self.btn_prev = ModernButton(self.footer, text="< Previous Step", command=self.prev_step, primary=False)
        self.btn_prev.pack(side=tk.LEFT, padx=20, pady=20)
        
        self.btn_next = ModernButton(self.footer, text="Next Step >", command=self.next_step, primary=True)
        self.btn_next.pack(side=tk.RIGHT, padx=20, pady=20)
        
        self.lbl_counter = tk.Label(self.footer, text="0 / 0", bg=Colors.BACKGROUND, fg=Colors.TEXT_DIM, font=Fonts.STATUS)
        self.lbl_counter.pack(side=tk.TOP, pady=30)
        
    def _on_resize(self, event):
        self.after_cancel(getattr(self, '_resize_job', '')) if hasattr(self, '_resize_job') else None
        self._resize_job = self.after(100, lambda: self._show_step(self.current_step))

    def _show_step(self, index):
        if not self.debug_frames:
            return
            
        if index < 0: index = 0
        if index >= len(self.debug_frames): index = len(self.debug_frames) - 1
        self.current_step = index
        
        frame = self.debug_frames[index]
        
        self.lbl_title.config(text=f"Step {index}: {frame['title']}")
        self.lbl_desc.config(text=frame['desc'])
        self.lbl_counter.config(text=f"{index + 1} / {len(self.debug_frames)}")
        
        self.btn_prev.set_disabled(index <= 0)
        self.btn_next.set_disabled(index >= len(self.debug_frames) - 1)
        
        # Display Image
        pil_img = frame['image']
        
        win_w = self.content_frame.winfo_width()
        win_h = self.content_frame.winfo_height()
        
        if win_w > 1 and win_h > 1:
            w, h = pil_img.size
            ratio = min(win_w/w, win_h/h)
            
            if ratio > 1 and ratio < 2: ratio = 1
                
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            
            if new_w > 0 and new_h > 0:
                resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self.tk_img = ImageTk.PhotoImage(resized)
                self.image_label.config(image=self.tk_img)
        else:
            pass

    def next_step(self):
        self._show_step(self.current_step + 1)

    def prev_step(self):
        self._show_step(self.current_step - 1)
