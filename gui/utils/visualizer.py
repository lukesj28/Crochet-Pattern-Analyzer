import cv2
import numpy as np

def draw_spine(image, spine_points, color=(0, 255, 0), thickness=8):
    if not spine_points:
        return image
        
    pts = np.array(spine_points, np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(image, [pts], False, color, thickness)
    return image

def draw_width_line(image, p1, p2, color=(255, 0, 0), thickness=8):
    cv2.line(image, p1, p2, color, thickness)
    return image

def draw_corners(image, corners, color=(0, 0, 255), radius=20):
    if not corners:
        return image
        
    for x, y in corners:
        cv2.circle(image, (x, y), radius, color, -1)
        
    return image

def draw_stitch_votes(image, stitch_votes):
    for (sx, sy), (b_vx, b_vy), (s_vx, s_vy) in stitch_votes:
        scale = 80 
        
        b_end_x = int(sx + b_vx * scale)
        b_end_y = int(sy + b_vy * scale)
        cv2.arrowedLine(image, (sx, sy), (b_end_x, b_end_y), (255, 255, 0), 8, tipLength=0.5)
        
        if s_vx != 0 or s_vy != 0:
            s_end_x = int(sx + s_vx * scale)
            s_end_y = int(sy + s_vy * scale)
            cv2.arrowedLine(image, (sx, sy), (s_end_x, s_end_y), (255, 0, 255), 8, tipLength=0.5)
            
    return image

def draw_spine_arrows(image, spine_points, global_dir, spacing=200):
    if not spine_points:
        return image
        
    step = spacing 
    
    points_to_draw = spine_points if global_dir == 1 else spine_points[::-1]
    
    for i in range(0, len(points_to_draw), step):
        if i + 10 >= len(points_to_draw): break
        
        p1 = points_to_draw[i]
        p2 = points_to_draw[i+10]
        
        cv2.arrowedLine(image, p1, p2, (0, 255, 0), 10, tipLength=4)
        
    return image
