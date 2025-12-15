import cv2
import numpy as np
import preprocessing.filters as filters

def detect_stitches(image, mask, spine_points, yarn_width, max_corners=100, quality_level=0.05, debug=False):
    if not spine_points or yarn_width is None:
        return ([], {}) if debug else []

    # Sharpening
    sharpened_img = filters.apply_unsharp_mask(image, strength=0.5)

    # Prepare Grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Compute Spine Map
    dist_map = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    cv2.normalize(dist_map, dist_map, 0, 1.0, cv2.NORM_MINMAX)
    
    # Spine Weighting
    weight_map = np.power(dist_map, 4.0)
    
    # Apply Weighting
    gray_float = gray.astype(np.float32) / 255.0
    weighted_img = gray_float * weight_map
    
    # Optimization range
    start_dist = int(yarn_width * 0.5)
    end_dist = int(yarn_width * 1.5)
    
    start_dist = max(5, start_dist)
    if end_dist <= start_dist:
        end_dist = start_dist + 10

    best_score = float('inf')
    best_corners = []
    optimization_steps = []
    
    spine_arr = np.array(spine_points)
    
    for test_dist in range(start_dist, end_dist + 1, 10):
        corners = cv2.goodFeaturesToTrack(
            weighted_img,
            maxCorners=max_corners,
            qualityLevel=quality_level,
            minDistance=test_dist,
            blockSize=9,
            useHarrisDetector=False
        )
        
        if corners is None or len(corners) < 3: 
            continue
            
        pts = [tuple(c[0]) for c in np.int32(corners)]
        
        # Project to Spine & Sort
        spine_indices = []
        for cx, cy in pts:
            dists = np.sum((spine_arr - np.array([cx, cy]))**2, axis=1)
            idx = np.argmin(dists)
            spine_indices.append(idx)
            
        spine_indices.sort()
        
        # Calculate Intervals
        intervals = np.diff(spine_indices)
        
        if len(intervals) == 0: continue
            
        mean_i = np.mean(intervals)
        std_i = np.std(intervals)
        
        if mean_i == 0: continue
            
        cv_val = std_i / mean_i
        
        # Add bias
        target = yarn_width
        bias = abs(test_dist - target) / target
        
        score = cv_val + (bias * 0.5)
        
        if debug:
            step_img = image.copy()
            for cx, cy in pts:
                cv2.circle(step_img, (cx, cy), 5, (0, 255, 255), -1)
            
            optimization_steps.append({
                'dist': test_dist,
                'score': score,
                'cv': cv_val,
                'corners': pts,
                'image': step_img
            })

        if score < best_score:
            best_score = score
            best_corners = pts
            
    # Refine positions
    refined_corners = []
    if best_corners:
        radius = int(yarn_width / 2)
        if radius < 3: radius = 3
        
        snap_gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        
        h, w = gray.shape
        
        for cx, cy in best_corners:
            x1 = max(0, cx - radius)
            y1 = max(0, cy - radius)
            x2 = min(w, cx + radius + 1)
            y2 = min(h, cy + radius + 1)
            
            roi = snap_gray[y1:y2, x1:x2]
            if roi.size == 0:
                refined_corners.append((cx, cy))
                continue
                
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(roi)
            
            final_x = x1 + min_loc[0]
            final_y = y1 + min_loc[1]
            
            refined_corners.append((final_x, final_y))
            
    if debug:
        weight_map_visual = (weight_map * 255).astype(np.uint8)
        heatmap_img = cv2.applyColorMap(weight_map_visual, cv2.COLORMAP_JET)
        
        return refined_corners, {
            'heatmap': heatmap_img,
            'steps': optimization_steps,
            'raw': best_corners
        }

    return refined_corners
