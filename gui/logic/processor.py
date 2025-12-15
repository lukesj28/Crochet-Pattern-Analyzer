import cv2
import numpy as np
from PIL import Image, ImageOps

import preprocessing.hue_isolator as hue_isolator
import preprocessing.filters as filters
import postprocessing.yarn_framing as yarn_framing
import postprocessing.stitch_detection as stitch_detection
import postprocessing.direction_detection as direction_detection
import gui.utils.visualizer as visualizer

class ImageProcessor:
    def __init__(self):
        self.original_cv_image = None
        self.blurred_cv_image = None
        self.masked_processing_image = None
        self.current_mask = None
        self.yarn_width = None
        self.debug_frames = []
    
    def load_image(self, file_path):
        self.reset_state()
        
        try:
            # Load and Orient
            pil_img = Image.open(file_path)
            pil_img = ImageOps.exif_transpose(pil_img)
            
            if pil_img.mode == 'RGB':
                open_cv_image = np.array(pil_img) 
                open_cv_image = open_cv_image[:, :, ::-1].copy() 
            elif pil_img.mode == 'RGBA':
                open_cv_image = np.array(pil_img) 
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
            else: 
                 open_cv_image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_GRAY2BGR)

            self.original_cv_image = open_cv_image
            
            self.blurred_cv_image = filters.apply_bilateral_filter(self.original_cv_image)
            
            self.debug_frames.append({
                'title': "Original Image",
                'image': self._cv_to_pil(self.original_cv_image),
                'desc': "The raw input image loaded from disk."
            })
            self.debug_frames.append({
                'title': "Blurred Image",
                'image': self._cv_to_pil(self.blurred_cv_image),
                'desc': "Bilateral filter applied to reduce noise while preserving edges."
            })
            
            return pil_img
            
        except Exception:
            raise

    def process_click_at(self, x, y):
        if self.blurred_cv_image is None:
            return None

        color_name = hue_isolator.get_dominant_color_name(self.blurred_cv_image, x, y)
        
        if color_name:
            self.current_mask = hue_isolator.get_isolation_mask(self.blurred_cv_image, color_name, (x, y))
            
            self.masked_processing_image = hue_isolator.apply_mask_to_image(
                self.blurred_cv_image, self.current_mask, darken_factor=0.0
            )
            
            self.debug_frames = self.debug_frames[:2] 
            self.debug_frames.append({
                'title': "Isolated Yarn (Masked)",
                'image': self._cv_to_pil(self.masked_processing_image),
                'desc': "Yarn isolated from background using hue detection. Background set to black."
            })
            
            display_cv = hue_isolator.apply_mask_to_image(
                self.original_cv_image, self.current_mask, darken_factor=0.4
            )
            
            return self._cv_to_pil(display_cv)
        
        return None

    def run_full_analysis(self):
        if self.current_mask is None or self.masked_processing_image is None:
            return None, None
            
        processing_img = self.masked_processing_image
        report_data = None
        
        display_cv = hue_isolator.apply_mask_to_image(
            self.original_cv_image, self.current_mask, darken_factor=0.4
        )
        
        spine_points, skeleton_img = yarn_framing.find_spine(processing_img, return_skeleton=True)
        
        if spine_points:
            # Yarn Framing (Spine)
            visualizer.draw_spine(display_cv, spine_points)

            # Measure Width
            width_info = yarn_framing.measure_width_at_center(spine_points, self.current_mask)
            
            # Spine & Skeleton Visualization
            step3_left = processing_img.copy()
            visualizer.draw_spine(step3_left, spine_points)
            if width_info:
                p1, p2, half_width = width_info
                self.yarn_width = half_width
                visualizer.draw_width_line(step3_left, p1, p2)
                visualizer.draw_width_line(display_cv, p1, p2)
            
            step3_right = cv2.cvtColor(skeleton_img, cv2.COLOR_GRAY2BGR)
            
            h, w, _ = step3_left.shape
            combined = np.hstack((step3_left, step3_right))
            
            self.debug_frames.append({
                'title': "Spine Extraction",
                'image': self._cv_to_pil(combined),
                'desc': "Left: Spine & Width detected on isolated image. Right: Skeleton used for pathfinding."
            })
            
            # Detect Stitches
            if self.yarn_width is not None:
                stitches, debug_data = stitch_detection.detect_stitches(
                    processing_img, 
                    self.current_mask, 
                    spine_points, 
                    self.yarn_width,
                    debug=True
                )
                
                heatmap_img = debug_data.get('heatmap')
                opt_steps = debug_data.get('steps', [])
                raw_pts = debug_data.get('raw', [])
                snapped_pts = stitches
                
                # Heat Map Visualization
                if heatmap_img is not None:
                    self.debug_frames.append({
                        'title': "Distance Transform Heatmap",
                        'image': self._cv_to_pil(heatmap_img),
                        'desc': "Weighting map based on distance from center (spine) and yarn edges."
                    })
                    
                # Optimization Steps Visualization
                if opt_steps:
                    indices = [0, len(opt_steps)//2, len(opt_steps)-1]
                    indices = sorted(list(set(indices))) 
                    
                    combined_opt_list = []
                    descriptions = []
                    
                    for idx in indices:
                        step = opt_steps[idx]
                        desc = f"d={step['dist']}, cv={step['cv']:.2f}"
                        descriptions.append(desc)
                        
                        clean_img = processing_img.copy()
                        visualizer.draw_corners(clean_img, step['corners'], color=(0, 255, 255), radius=20)
                        
                        cv2.putText(clean_img, desc, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        
                        combined_opt_list.append(clean_img)
                    
                    if combined_opt_list:
                        combined_opt_img = np.hstack(combined_opt_list)
                        self.debug_frames.append({
                            'title': f"Optimization Iterations",
                            'image': self._cv_to_pil(combined_opt_img),
                            'desc': f"Comparing corner spacing consistency (CV) at different minimum distances: {', '.join(descriptions)}"
                        })

                # Stitch Refinement Visualization
                left_img = processing_img.copy()
                visualizer.draw_corners(left_img, raw_pts, color=(0, 255, 255), radius=15) 
                
                right_img = processing_img.copy()
                visualizer.draw_corners(right_img, snapped_pts, color=(0, 0, 255), radius=15)
                
                combined_stitches = np.hstack((left_img, right_img))
                self.debug_frames.append({
                    'title': "Stitch Refinement",
                    'image': self._cv_to_pil(combined_stitches),
                    'desc': "Left: Raw Optimization Results (Cyan). Right: Snapped to Darkest Pixels (Red)."
                })
                if stitches:
                    # Determine Direction
                    gray_proc = cv2.cvtColor(processing_img, cv2.COLOR_BGR2GRAY)
                    
                    global_dir, votes, mean_vec = direction_detection.determine_direction(
                        gray_proc, 
                        spine_points, 
                        stitches, 
                        self.yarn_width
                    )
                    
                    # Convert Mean Vector to Cardinal Direction
                    mx, my = mean_vec
                    abs_x = abs(mx)
                    abs_y = abs(my)
                    
                    dir_text = "UNKNOWN"
                    if abs_x > abs_y:
                        dir_text = "RIGHT" if mx > 0 else "LEFT"
                    else:
                        dir_text = "DOWN" if my > 0 else "UP"

                    # Check Visual Alignment of Spine Arrows
                    visual_dir_text = direction_detection.check_visual_spine_direction(
                        processing_img.shape, spine_points, global_dir
                    )
                    
                    # Flip logic if strictly opposite
                    flipped_visual = False
                    if dir_text == "LEFT" and visual_dir_text == "RIGHT":
                        global_dir *= -1
                        flipped_visual = True
                    elif dir_text == "RIGHT" and visual_dir_text == "LEFT":
                        global_dir *= -1
                        flipped_visual = True
                    elif dir_text == "UP" and visual_dir_text == "DOWN":
                        global_dir *= -1
                        flipped_visual = True
                    elif dir_text == "DOWN" and visual_dir_text == "UP":
                        global_dir *= -1
                        flipped_visual = True

                    # Map visual arrows to use raw points while keeping direction calculation from snapped points
                    visual_votes = votes
                    if raw_pts and len(raw_pts) == len(votes):
                        visual_votes = []
                        for i in range(len(votes)):
                            _, vb, vs = votes[i]
                            visual_votes.append((raw_pts[i], vb, vs))

                    # CAPTURE STEP 7: Stitch Directions
                    step7_img = processing_img.copy()
                    visualizer.draw_stitch_votes(step7_img, visual_votes) # Start arrows at Raw
                    # Also draw Raw dots instead of snapped stitches
                    final_dots = raw_pts if raw_pts else stitches
                    visualizer.draw_corners(step7_img, final_dots, color=(0, 0, 255), radius=20)
                    
                    self.debug_frames.append({
                        'title': "Stitch Direction Analysis",
                        'image': self._cv_to_pil(step7_img),
                        'desc': "Cyan Arrows: Brightness Gradient. Pink Arrows: Structure Tensor (if active). Calculating local flow at each stitch."
                    })

                    # Drawing Layer 2: Spine Arrows
                    visualizer.draw_spine_arrows(display_cv, spine_points, global_dir)
                    
                    # CAPTURE STEP 8: Spine Direction
                    step8_img = processing_img.copy()
                    visualizer.draw_spine(step8_img, spine_points) # Added spine line for context
                    visualizer.draw_spine_arrows(step8_img, spine_points, global_dir)
                    
                    flip_msg = f" (Visual Correction applied: {visual_dir_text} -> Adjusted)" if flipped_visual else ""
                    self.debug_frames.append({
                        'title': "Global Spine Flow",
                        'image': self._cv_to_pil(step8_img),
                        'desc': f"Global Direction Determined: {dir_text} (Mean Vector: [{mx:.2f}, {my:.2f}]). Green arrows follow the loop structure.{flip_msg}"
                    })
                    
                    # Drawing Layer 3: Stitch Arrows
                    visualizer.draw_stitch_votes(display_cv, visual_votes) # Use mapped votes
                    
                    # Drawing Layer 4: Stitch Dots (Top)
                    # User Request: Use raw points (not snapped) for final dot visualization
                    visualizer.draw_corners(display_cv, final_dots, color=(0, 0, 255), radius=20)
                     # For consistency in main view too
                    
                    # CAPTURE STEP 9: Final Result
                    self.debug_frames.append({
                        'title': "Final Analysis Output",
                        'image': self._cv_to_pil(display_cv),
                        'desc': "Complete visualization with Spine, Width, Flow Arrows, and Stitch Locations (Raw) overlaid on the original image."
                    })
                    
                    # Prepare Report Data
                    report_data = {
                        "count": len(stitches),
                        "direction": dir_text,
                        "width": self.yarn_width * 2 # Full width
                    }
        
        return self._cv_to_pil(display_cv), report_data

    def reset_state(self):
        self.original_cv_image = None
        self.blurred_cv_image = None
        self.masked_processing_image = None
        self.current_mask = None
        self.yarn_width = None
        self.debug_frames = []

    def has_image(self):
        return self.original_cv_image is not None

    def _cv_to_pil(self, cv_img):
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(img_rgb)
