import cv2
import numpy as np
from skimage.morphology import skeletonize
import networkx as nx

def find_spine(image, return_skeleton=False):
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
        
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    binary_bool = binary > 0
    
    skeleton = skeletonize(binary_bool)
    
    y_idxs, x_idxs = np.where(skeleton)
    points = list(zip(x_idxs, y_idxs))
    
    if return_skeleton:
        skeleton_uint8 = (skeleton * 255).astype(np.uint8)
    
    if not points:
        return ([], skeleton_uint8) if return_skeleton else []
        
    G = nx.Graph()
    for p in points:
        G.add_node(p)
        
    point_set = set(points)
    for x, y in points:
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx_coord = x + dx
                ny_coord = y + dy
                neighbor = (nx_coord, ny_coord)
                
                if neighbor in point_set:
                    dist = np.sqrt(dx*dx + dy*dy)
                    G.add_edge((x, y), neighbor, weight=dist)

    degrees = dict(G.degree())
    leaves = [n for n, d in degrees.items() if d == 1]
    
    if len(leaves) < 2:
        if not points:
            return ([], skeleton_uint8) if return_skeleton else []
        leaves = [points[0]]
        
    def get_furthest_node(start_node):
        lengths = nx.single_source_dijkstra_path_length(G, start_node, weight='weight')
        max_node = max(lengths, key=lengths.get)
        return max_node, lengths[max_node]

    start_node = leaves[0]
    far_node, _ = get_furthest_node(start_node)
    end_node, _ = get_furthest_node(far_node)
    
    path = nx.shortest_path(G, far_node, end_node, weight='weight')
    
    if return_skeleton:
        return path, skeleton_uint8
    return path

def measure_width_at_center(spine_points, mask):
    if not spine_points or len(spine_points) < 2:
        return None
        
    center_idx = len(spine_points) // 2
    center_pt = spine_points[center_idx]
    cx, cy = center_pt
    
    # Calculate Tangent
    delta = 5
    p_start = spine_points[max(0, center_idx - delta)]
    p_end = spine_points[min(len(spine_points) - 1, center_idx + delta)]
    
    dx = p_end[0] - p_start[0]
    dy = p_end[1] - p_start[1]
    
    length = np.sqrt(dx*dx + dy*dy)
    if length == 0:
        return None
        
    ux = dx / length
    uy = dy / length
    
    # Calculate Normal (-y, x)
    nx_vec = -uy
    ny_vec = ux
    
    # Raycast to find edges
    h, w = mask.shape
    
    def cast_ray(start_x, start_y, dir_x, dir_y):
        curr_x, curr_y = start_x, start_y
        while 0 <= int(curr_x) < w and 0 <= int(curr_y) < h:
            if mask[int(curr_y), int(curr_x)] == 0:
                break
            curr_x += dir_x
            curr_y += dir_y
        return (int(curr_x), int(curr_y))

    p1 = cast_ray(cx, cy, nx_vec, ny_vec)
    p2 = cast_ray(cx, cy, -nx_vec, -ny_vec)
    
    full_dist = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    half_width = full_dist / 2.0
    
    return p1, p2, half_width
