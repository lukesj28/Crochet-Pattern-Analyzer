import tkinter as tk
from tkinter import filedialog, messagebox
import gui.ui.image_viewer as image_viewer
import gui.logic.processor as processor
import gui.ui.report_panel as report_panel
import gui.ui.pipeline_viewer as pipeline_viewer
from gui.ui.theme import Colors, Fonts
from gui.ui.components import ModernButton, StatusLabel

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crochet Pattern Analyzer")
        
        self._setup_window()
        self.processor = processor.ImageProcessor()
        
        self.main_container = tk.Frame(root, bg=Colors.BACKGROUND)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.header_frame = tk.Frame(self.main_container, bg=Colors.PANEL_BG, height=40)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.header_frame.pack_propagate(False)
        
        self.title_label = tk.Label(self.header_frame, text="PATTERN ANALYZER v1.0", 
                                    bg=Colors.PANEL_BG, fg=Colors.TEXT_DIM, font=Fonts.HEADER)
        self.title_label.pack(side=tk.LEFT, padx=15, pady=5)
        
        self.status_bar_frame = tk.Frame(self.main_container, bg=Colors.PANEL_BG, height=30)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar_frame.pack_propagate(False)
        
        self.status_label = StatusLabel(self.status_bar_frame, text="System Ready. Load an image to begin.")
        self.status_label.pack(side=tk.LEFT, padx=10, fill=tk.X)
        
        self.control_container = tk.Frame(self.main_container, bg=Colors.BACKGROUND, height=130)
        self.control_container.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))
        self.control_container.pack_propagate(False)
        
        self.report_panel = report_panel.ReportPanel(self.control_container)
        self.report_panel.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        
        self.control_frame = tk.Frame(self.control_container, bg=Colors.BACKGROUND)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        self.display_container = tk.Frame(self.main_container, bg=Colors.BORDER, padx=1, pady=1)
        self.display_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=(10, 0))
        
        self.display_frame = tk.Frame(self.display_container, bg=Colors.CANVAS_BG)
        self.display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.viewer = image_viewer.ImageViewer(self.display_frame)
        self.viewer.set_click_callback(self.on_image_click)
        
        self._setup_controls()
        self.reset_app()
        
    def _setup_window(self):
        window_width = 900
        window_height = 800
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.configure(bg=Colors.BACKGROUND)
        
    def _setup_controls(self):
        self.btn_load = ModernButton(self.display_frame, text="LOAD SOURCE IMAGE", 
                                     command=self.open_image, primary=True)
        
        self.btn_continue = ModernButton(self.control_frame, text="ANALYZE", 
                                         command=self.run_analysis, primary=True)
        
        self.btn_reset = ModernButton(self.control_frame, text="RESET", 
                                      command=self.reset_app, primary=False)
                                      
        self.btn_pipeline = ModernButton(self.control_frame, text="VIEW STEPS", 
                                         command=self.open_pipeline_viewer, primary=False)
    
    def reset_app(self):
        self.processor.reset_state()
        self.viewer.clear()
        self.report_panel.reset_report()
        
        self.btn_continue.pack_forget()
        self.btn_reset.pack_forget()
        self.btn_pipeline.pack_forget()
        
        self.btn_load.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.status_label.set_status("Waiting for input source...")

    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Analysis Source",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if file_path:
            try:
                self.status_label.set_status("Preprocessing image...", "warning")
                self.root.update()
                
                # Processor loads logic
                pil_img = self.processor.load_image(file_path)
                
                # Viewer displays
                self.viewer.display_image(pil_img)
                self.btn_load.place_forget()
                
                self.status_label.set_status("Image Loaded. Click on the yarn to isolate specific hue.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open image: {e}")
                self.status_label.set_status("Error loading image.", "error")

    def on_image_click(self, x, y):
        # Isolation Phase check
        if self.btn_reset.winfo_ismapped() and not self.btn_continue.winfo_ismapped():
            return
            
        if not self.processor.has_image():
            return

        # Delegate to Processor
        preview_img = self.processor.process_click_at(x, y)
        
        if preview_img:
            self.viewer.display_image(preview_img)
            self.status_label.set_status("Hue Isolated. Ready to process geometry.", "success")
            
            # Show Controls
            if not self.btn_continue.winfo_ismapped():
                self.btn_continue.pack(side=tk.RIGHT, padx=20)
                self.btn_reset.pack(side=tk.RIGHT, padx=0) 

    def run_analysis(self):
        self.status_label.set_status("Executing detection algorithms...", "warning")
        self.root.update()
        
        # Delegate to Processor
        result_img, report_data = self.processor.run_full_analysis()
        
        if result_img:
            self.viewer.display_image(result_img)
            
            # Update Report
            if report_data:
                self.report_panel.update_report(
                    stitch_count=report_data['count'],
                    direction_text=report_data['direction'],
                    width_px=report_data['width']
                )
            
            # Update Controls
            self.btn_continue.pack_forget()
            
            self.btn_reset.pack_forget()
            self.btn_reset.pack(side=tk.RIGHT, padx=20)
            self.btn_pipeline.pack(side=tk.LEFT, padx=20)
            
            self.status_label.set_status("Analysis Complete.", "success")
            
    def open_pipeline_viewer(self):
        if not self.processor.debug_frames:
            messagebox.showinfo("Info", "No pipeline data available.")
            return
            
        viewer = pipeline_viewer.PipelineViewer(self.root, self.processor.debug_frames)
