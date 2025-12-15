import tkinter as tk
from PIL import ImageTk, Image

from gui.ui.theme import Colors

class ImageViewer:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        
        self.panel = tk.Label(self.parent, bg=Colors.CANVAS_BG)
        self.panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.tk_image = None
        self.scale_ratio = 1.0
        self.scaled_size = (0, 0)
        self.current_pil_image = None
        
        self.on_click_callback = None
        
        self.panel.bind("<Button-1>", self._handle_click)

    def set_click_callback(self, callback):
        self.on_click_callback = callback

    def display_image(self, pil_img):
        self.parent.update_idletasks()
        
        frame_width = self.parent.winfo_width()
        frame_height = self.parent.winfo_height()
        
        if frame_width <= 1: frame_width = 600 
        if frame_height <= 1: frame_height = 500

        img_width, img_height = pil_img.size
        
        self.scale_ratio = min(frame_width / img_width, frame_height / img_height)
        
        new_width = int(img_width * self.scale_ratio)
        new_height = int(img_height * self.scale_ratio)
        self.scaled_size = (new_width, new_height)
        
        if new_width > 0 and new_height > 0:
            resized_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized_img = pil_img
            
        self.current_pil_image = resized_img
        self.tk_image = ImageTk.PhotoImage(resized_img)
        
        self.panel.config(image=self.tk_image)
        self.panel.image = self.tk_image

    def clear(self):
        self.panel.config(image='')
        self.panel.image = None
        self.tk_image = None
        self.current_pil_image = None
        self.scale_ratio = 1.0

    def _handle_click(self, event):
        if self.tk_image is None or self.on_click_callback is None:
            return

        label_width = self.panel.winfo_width()
        label_height = self.panel.winfo_height()
        img_w, img_h = self.scaled_size
        
        offset_x = (label_width - img_w) // 2
        offset_y = (label_height - img_h) // 2
        
        click_x = event.x - offset_x
        click_y = event.y - offset_y
        
        if 0 <= click_x < img_w and 0 <= click_y < img_h:
            orig_x = int(click_x / self.scale_ratio)
            orig_y = int(click_y / self.scale_ratio)
            self.on_click_callback(orig_x, orig_y)

    def get_widget_dimensions(self):
        return self.panel.winfo_width(), self.panel.winfo_height()
