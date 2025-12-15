import cv2
import numpy as np

def get_color_ranges(color_name):
    color = color_name.lower()
    
    # Define ranges (Lower, Upper)
    colors = {
        'red': [
            (np.array([0, 70, 50]), np.array([10, 255, 255])),
            (np.array([170, 70, 50]), np.array([180, 255, 255]))
        ],
        'orange': [(np.array([11, 70, 50]), np.array([25, 255, 255]))],
        'yellow': [(np.array([26, 70, 50]), np.array([35, 255, 255]))],
        'green': [(np.array([36, 70, 50]), np.array([85, 255, 255]))],
        'blue': [(np.array([86, 70, 50]), np.array([125, 255, 255]))],
        'purple': [(np.array([126, 70, 50]), np.array([150, 255, 255]))],
        'pink': [(np.array([151, 70, 50]), np.array([169, 255, 255]))],
        'cyan': [(np.array([80, 70, 50]), np.array([95, 255, 255]))], 
        'magenta': [(np.array([140, 70, 50]), np.array([160, 255, 255]))],
        'white': [(np.array([0, 0, 200]), np.array([180, 50, 255]))],
        'gray': [(np.array([0, 0, 50]), np.array([180, 50, 200]))],
        'black': [(np.array([0, 0, 0]), np.array([180, 255, 50]))]
    }
    
    return colors.get(color, [])

def get_color_name_from_hsv(h, s, v):
    if s < 60:
        if v < 40: return 'black'
        if v > 220: return 'white'
        return 'gray'
        
    if v < 40: return 'black'
    
    if (h >= 0 and h <= 10) or (h >= 170 and h <= 180): return 'red'
    if 11 <= h <= 25: return 'orange'
    if 26 <= h <= 35: return 'yellow'
    if 36 <= h <= 85: return 'green'
    if 86 <= h <= 125: return 'blue'
    if 126 <= h <= 150: return 'purple'
    if 151 <= h <= 169: return 'pink'
    
    if 80 <= h <= 95: return 'cyan'
    if 140 <= h <= 160: return 'magenta'
    
    return 'gray'

def get_dominant_color_name(image, x, y, kernel_size=5):
    h, w = image.shape[:2]
    
    x1 = max(0, x - kernel_size // 2)
    y1 = max(0, y - kernel_size // 2)
    x2 = min(w, x + kernel_size // 2 + 1)
    y2 = min(h, y + kernel_size // 2 + 1)
    
    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return None
        
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    avg_hsv = np.mean(hsv_roi, axis=(0, 1))
    
    return get_color_name_from_hsv(avg_hsv[0], avg_hsv[1], avg_hsv[2])

def isolate_color(image, color_name):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    ranges = get_color_ranges(color_name)
    
    if not ranges:
        return image
        
    mask_final = np.zeros(image.shape[:2], dtype="uint8")
    for (lower, upper) in ranges:
        mask = cv2.inRange(hsv, lower, upper)
        mask_final = cv2.bitwise_or(mask_final, mask)
        
    kernel = np.ones((3,3), np.uint8)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_OPEN, kernel, iterations=2)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    result = cv2.bitwise_and(image, image, mask=mask_final)
    
    return result

def keep_component_at_point(mask, point):
    h, w = mask.shape
    px, py = point
    if px < 0 or px >= w or py < 0 or py >= h:
        return mask
        
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    
    target_label = labels[py, px]
    
    if target_label == 0:
        return np.zeros_like(mask)

    new_mask = np.zeros_like(mask)
    new_mask[labels == target_label] = 255
    
    return new_mask

def get_isolation_mask(image, color_name, click_point=None):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    ranges = get_color_ranges(color_name)
    
    if not ranges:
        return np.zeros(image.shape[:2], dtype="uint8")
        
    mask_final = np.zeros(image.shape[:2], dtype="uint8")
    for (lower, upper) in ranges:
        mask = cv2.inRange(hsv, lower, upper)
        mask_final = cv2.bitwise_or(mask_final, mask)
        
    # Clean up mask (Dilation followed by Erosion)
    kernel = np.ones((3,3), np.uint8)
    mask_final = cv2.dilate(mask_final, kernel, iterations=5)
    mask_final = cv2.erode(mask_final, kernel, iterations=3)
    
    # Closing
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, iterations=4)
    
    # Filter by connected component
    if click_point:
        mask_final = keep_component_at_point(mask_final, click_point)
        
    # Fill Holes
    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cv2.drawContours(mask_final, contours, -1, 255, thickness=cv2.FILLED)
 
    # Smooth Edges
    smooth_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, smooth_kernel)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_OPEN, smooth_kernel)

    return mask_final

def apply_mask_to_image(image, mask, darken_factor=0.0):
    if darken_factor == 0.0:
        return cv2.bitwise_and(image, image, mask=mask)
        
    fg = cv2.bitwise_and(image, image, mask=mask)
    
    mask_inv = cv2.bitwise_not(mask)
    bg = cv2.bitwise_and(image, image, mask=mask_inv)
    bg = (bg * darken_factor).astype(np.uint8)
    
    return cv2.add(fg, bg)
