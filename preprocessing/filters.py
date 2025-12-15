import cv2

def apply_bilateral_filter(image, d=9, sigma_color=150, sigma_space=150):
    return cv2.bilateralFilter(image, d, sigma_color, sigma_space)

def apply_unsharp_mask(image, strength=2.0):
    # Use standard bilateral parameters for the mask generation
    blur = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
    
    sharpened = cv2.addWeighted(image, 1.0 + strength, blur, -strength, 0)
    
    return sharpened

def apply_clahe(image, clip_limit=2.0, tile_grid_size=(8,8)):
    # Convert to LAB (Lightness serves as intensity)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L-channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l)
    
    # Merge and Convert back
    limg = cv2.merge((cl, a, b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    
    return final
