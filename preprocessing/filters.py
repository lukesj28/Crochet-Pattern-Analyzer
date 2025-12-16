import cv2

def apply_bilateral_filter(image, d=9, sigma_color=150, sigma_space=150):
    return cv2.bilateralFilter(image, d, sigma_color, sigma_space)

def apply_unsharp_mask(image, strength=2.0):
    # Use standard bilateral parameters for the mask generation
    blur = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
    
    sharpened = cv2.addWeighted(image, 1.0 + strength, blur, -strength, 0)
    
    return sharpened
