import cv2
import numpy as np
import math

def get_structural_vector(image, cx, cy, radius):
    h, w = image.shape
    roi_size = radius * 2
    half = radius
    
    x1 = max(0, cx - half)
    y1 = max(0, cy - half)
    x2 = min(w, cx + half + 1)
    y2 = min(h, cy + half + 1)
    
    roi = image[y1:y2, x1:x2]
    if roi.size == 0 or roi.shape[0] < 2 or roi.shape[1] < 2:
        return 0, 0
        
    try:
        gX = cv2.Sobel(roi, cv2.CV_32F, 1, 0, ksize=3)
        gY = cv2.Sobel(roi, cv2.CV_32F, 0, 1, ksize=3)
    except:
        return 0, 0
        
    # Structure Tensor elements
    Jxx = np.sum(gX * gX)
    Jyy = np.sum(gY * gY)
    Jxy = np.sum(gX * gY)
    
    # Angle of Structure
    theta = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    struct_angle = theta + (np.pi / 2)
    
    vx = math.cos(struct_angle)
    vy = math.sin(struct_angle)
    
    # Resolve ambiguity using Intensity Centroid
    M = cv2.moments(roi)
    if M["m00"] != 0:
        cX_local = (M["m10"] / M["m00"])
        cY_local = (M["m01"] / M["m00"])
        
        center_x = cx - x1
        center_y = cy - y1
        
        vec_to_mass_x = cX_local - center_x
        vec_to_mass_y = cY_local - center_y
        
        dot = vx * vec_to_mass_x + vy * vec_to_mass_y
        
        if dot > 0:
            vx = -vx
            vy = -vy
            
    return vx, vy

def get_brightness_vote(image, cx, cy, radius, tx, ty):
    h, w = image.shape
    x1 = max(0, cx - radius)
    y1 = max(0, cy - radius)
    x2 = min(w, cx + radius + 1)
    y2 = min(h, cy + radius + 1)
    
    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return 0
        
    y_indices, x_indices = np.mgrid[y1:y2, x1:x2]
    dx = x_indices - cx
    dy = y_indices - cy
    dist_sq = dx*dx + dy*dy
    mask_circle = dist_sq <= radius*radius
    dot = dx * tx + dy * ty
    
    mask_fwd = mask_circle & (dot > 0)
    mask_bwd = mask_circle & (dot <= 0)
    
    if np.count_nonzero(mask_fwd) > 0 and np.count_nonzero(mask_bwd) > 0:
        mean_fwd = np.mean(roi[mask_fwd])
        mean_bwd = np.mean(roi[mask_bwd])
        
        # Darker side wins
        if mean_fwd < mean_bwd:
            return 1 # Matches tangent
        else:
            return -1 # Opposes tangent
            
    return 0

def determine_direction(image_gray, spine_points, stitches, yarn_width):
    if not stitches or not spine_points:
        return 0, []

    spine_arr = np.array(spine_points)
    radius = int(yarn_width / 4)
    if radius < 3: radius = 3
    
    total_votes = 0
    stitch_vote_data = [] 
    
    h, w = image_gray.shape
    
    for sx, sy in stitches:
        # Local Spine Tangent
        dists = np.sum((spine_arr - np.array([sx, sy]))**2, axis=1)
        idx = np.argmin(dists)
        
        if idx < len(spine_points) - 1:
            tx = spine_points[idx+1][0] - spine_points[idx][0]
            ty = spine_points[idx+1][1] - spine_points[idx][1]
        elif idx > 0:
            tx = spine_points[idx][0] - spine_points[idx-1][0]
            ty = spine_points[idx][1] - spine_points[idx-1][1]
        else:
            tx, ty = 0, 0
            
        mag = np.sqrt(tx*tx + ty*ty)
        if mag == 0: continue
        tx, ty = tx/mag, ty/mag
        
        # Method 1: Darkest Half (Intensity Split)
        vote1 = get_brightness_vote(image_gray, sx, sy, radius, tx, ty)
                    
        # Method 2: Structure Tensor
        vote2 = 0
        vx_struct, vy_struct = get_structural_vector(image_gray, sx, sy, radius)
        
        # Check alignment with Tangent
        dot_struct = vx_struct * tx + vy_struct * ty
        if dot_struct > 0:
            vote2 = 1
        elif dot_struct < 0:
            vote2 = -1
            
        # Aggregate
        final_stitch_vote = vote1 + vote2
        total_votes += final_stitch_vote
        
        # Vectors for Visualization
        vis_b_dir = 1 if vote1 >= 0 else -1 
        vec_brightness = (tx * vis_b_dir, ty * vis_b_dir)
        
        vec_structure = (vx_struct, vy_struct)
        
        stitch_vote_data.append(((sx, sy), vec_brightness, vec_structure))

    global_direction = 1 if total_votes >= 0 else -1
    
    # Calculate Mean Global Vector
    sum_vx = 0.0
    sum_vy = 0.0
    
    for (_, (bx, by), (sx, sy)) in stitch_vote_data:
        sum_vx += bx
        sum_vy += by
        
    count = len(stitch_vote_data)
    if count > 0:
        mean_vx = sum_vx / count
        mean_vy = sum_vy / count
    else:
        mean_vx, mean_vy = 0.0, 0.0
        
    return global_direction, stitch_vote_data, (mean_vx, mean_vy)

def check_visual_spine_direction(image_shape, spine_points, global_dir, step=30):
    h, w = image_shape[:2]
    spine_arr = np.array(spine_points)
    
    hits = {'LEFT': 0, 'RIGHT': 0, 'UP': 0, 'DOWN': 0}
    
    for i in range(0, len(spine_points), step):
        pt = spine_points[i]
        
        # Calculate Tangent
        if i + 5 < len(spine_points):
            next_pt = spine_points[i+5]
            dx = next_pt[0] - pt[0]
            dy = next_pt[1] - pt[1]
        elif i - 5 >= 0:
            prev_pt = spine_points[i-5]
            dx = pt[0] - prev_pt[0]
            dy = pt[1] - prev_pt[1]
        else:
            continue
            
        mag = math.sqrt(dx*dx + dy*dy)
        if mag == 0: continue
        
        # Apply Global Direction
        dx = (dx / mag) * global_dir
        dy = (dy / mag) * global_dir
        
        # Raycast to Wall
        # Find distance to each wall
        dist_left = -1
        dist_right = -1
        dist_up = -1
        dist_down = -1
        
        if dx < 0: dist_left = pt[0] / abs(dx)
        if dx > 0: dist_right = (w - pt[0]) / abs(dx)
        if dy < 0: dist_up = pt[1] / abs(dy)
        if dy > 0: dist_down = (h - pt[1]) / abs(dy)
        
        # Find valid minimum positive distance
        candidates = []
        if dist_left >= 0: candidates.append((dist_left, 'LEFT'))
        if dist_right >= 0: candidates.append((dist_right, 'RIGHT'))
        if dist_up >= 0: candidates.append((dist_up, 'UP'))
        if dist_down >= 0: candidates.append((dist_down, 'DOWN'))
        
        if not candidates: continue
            
        _, wall = min(candidates, key=lambda x: x[0])
        hits[wall] += 1
        
    return max(hits, key=hits.get)
