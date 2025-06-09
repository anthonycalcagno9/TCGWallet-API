"""
Image comparison utilities for comparing card images.
"""
import io
import logging
import urllib.request
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)


def download_image(url: str) -> Optional[bytes]:
    """
    Download an image from a URL.
    
    Args:
        url: The URL of the image to download
        
    Returns:
        Image bytes or None if download fails
    """
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}")
        return None


def calculate_feature_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calculate similarity using ORB feature matching.
    This works better for comparing photos of cards against clean digital images.
    
    Args:
        img1: First image as numpy array
        img2: Second image as numpy array
        
    Returns:
        float: Feature similarity score (0-1 range)
    """
    try:
        # Convert to grayscale if needed
        if len(img1.shape) == 3:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        else:
            gray1 = img1
            
        if len(img2.shape) == 3:
            gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
        else:
            gray2 = img2
        
        # Ensure images are 8-bit
        gray1 = gray1.astype(np.uint8)
        gray2 = gray2.astype(np.uint8)
        
        # Create ORB detector with optimized settings for card matching
        orb = cv2.ORB_create(
            nfeatures=2000,        # More features for better matching
            scaleFactor=1.2,       # Fine scale pyramid
            nlevels=8,             # Good detail levels
            edgeThreshold=15,      # Lower threshold for more edge features
            firstLevel=0,          # Start from original scale
            WTA_K=2,              # Default
            scoreType=cv2.ORB_HARRIS_SCORE,  # Better corner detection
            patchSize=31,          # Good patch size for cards
            fastThreshold=20       # Tuned for card images
        )
        
        # Find keypoints and descriptors
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None:
            logger.debug("No descriptors found in one or both images")
            return 0.0
            
        if len(des1) < 5 or len(des2) < 5:
            logger.debug(f"Too few features: {len(des1) if des1 is not None else 0}, "
                        f"{len(des2) if des2 is not None else 0}")
            return 0.0
        
        # Create matcher with ratio test
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        
        # Match descriptors
        matches = bf.knnMatch(des1, des2, k=2)
        
        # Apply ratio test to filter good matches
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                # More lenient ratio test for card photos vs digital images
                if m.distance < 0.80 * n.distance:  # Slightly more lenient than 0.75
                    good_matches.append(m)
        
        if len(good_matches) == 0:
            return 0.0
            
        # Calculate feature similarity score with improved scoring
        total_features = max(len(kp1), len(kp2))
        match_ratio = len(good_matches) / total_features if total_features > 0 else 0
        
        # Average distance of good matches (normalized)
        avg_distance = sum(m.distance for m in good_matches) / len(good_matches)
        max_distance = 100  # Typical max distance for ORB
        distance_score = max(0, (max_distance - avg_distance) / max_distance)
        
        # Improved scoring that considers both match count and quality
        # More weight on having sufficient matches for cards
        if len(good_matches) >= 20:  # Good number of matches
            feature_score = (match_ratio * 3.0) * 0.7 + distance_score * 0.3
        elif len(good_matches) >= 10:  # Moderate matches
            feature_score = (match_ratio * 2.0) * 0.7 + distance_score * 0.3
        else:  # Few matches
            feature_score = (match_ratio * 1.5) * 0.6 + distance_score * 0.4
        
        logger.debug(f"Feature matching: {len(good_matches)} good matches, "
                    f"ratio={match_ratio:.3f}, avg_dist={avg_distance:.1f}, "
                    f"score={feature_score:.3f}")
        
        return min(1.0, feature_score)
        
    except Exception as e:
        logger.error(f"Error in feature similarity calculation: {e}")
        return 0.0


def calculate_histogram_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calculate similarity using color histogram comparison.
    This can help identify cards with similar color schemes.
    
    Args:
        img1: First image as numpy array
        img2: Second image as numpy array
        
    Returns:
        float: Histogram similarity score (0-1 range)
    """
    try:
        if len(img1.shape) == 3:
            # Use RGB histograms instead of HSV to avoid conversion issues
            # Calculate histograms for each channel
            hist1_r = cv2.calcHist([img1], [0], None, [256], [0, 256])
            hist1_g = cv2.calcHist([img1], [1], None, [256], [0, 256])
            hist1_b = cv2.calcHist([img1], [2], None, [256], [0, 256])
            
            hist2_r = cv2.calcHist([img2], [0], None, [256], [0, 256])
            hist2_g = cv2.calcHist([img2], [1], None, [256], [0, 256])
            hist2_b = cv2.calcHist([img2], [2], None, [256], [0, 256])
            
            # Normalize histograms
            hist1_r = hist1_r / np.sum(hist1_r)
            hist1_g = hist1_g / np.sum(hist1_g)
            hist1_b = hist1_b / np.sum(hist1_b)
            hist2_r = hist2_r / np.sum(hist2_r)
            hist2_g = hist2_g / np.sum(hist2_g)
            hist2_b = hist2_b / np.sum(hist2_b)
            
            # Calculate Chi-Square distance for better discrimination
            def chi_square_distance(h1, h2):
                return 0.5 * np.sum(((h1 - h2) ** 2) / (h1 + h2 + 1e-10))
            
            dist_r = chi_square_distance(hist1_r.flatten(), hist2_r.flatten())
            dist_g = chi_square_distance(hist1_g.flatten(), hist2_g.flatten())
            dist_b = chi_square_distance(hist1_b.flatten(), hist2_b.flatten())
            
            # Convert distance to similarity (0=identical, larger=more different)
            sim_r = np.exp(-dist_r)
            sim_g = np.exp(-dist_g)
            sim_b = np.exp(-dist_b)
            
            # Combine channels
            histogram_score = (sim_r + sim_g + sim_b) / 3.0
            
            logger.debug(f"Histogram similarity: R={sim_r:.3f}, G={sim_g:.3f}, "
                        f"B={sim_b:.3f}, Combined={histogram_score:.3f}")
            
        else:
            # Grayscale histogram
            hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])
            
            # Normalize
            hist1 = hist1 / np.sum(hist1)
            hist2 = hist2 / np.sum(hist2)
            
            # Chi-square distance
            dist = 0.5 * np.sum(((hist1 - hist2) ** 2) / (hist1 + hist2 + 1e-10))
            histogram_score = np.exp(-dist)
            
            logger.debug(f"Grayscale histogram: {histogram_score:.3f}")
        
        return max(0.0, min(1.0, histogram_score))
        
    except Exception as e:
        logger.error(f"Error in histogram similarity calculation: {e}")
        return 0.0


def calculate_template_matching(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calculate similarity using template matching.
    This helps find similar patterns even when images are at different scales/positions.
    
    Args:
        img1: First image as numpy array (grayscale)
        img2: Second image as numpy array (grayscale)
        
    Returns:
        float: Template matching score (0-1 range)
    """
    try:
        # If images are the same size, try both as template and source
        h1, w1 = img1.shape
        h2, w2 = img2.shape
        
        max_score = 0.0
        
        # Try different template matching methods
        methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
        
        for method in methods:
            try:
                if h1 == h2 and w1 == w2:
                    # Images are same size - direct comparison
                    result = cv2.matchTemplate(img1, img2, method)
                    _, score, _, _ = cv2.minMaxLoc(result)
                    max_score = max(max_score, score)
                else:
                    # Use smaller image as template
                    if h1 * w1 <= h2 * w2:
                        template = img1
                        source = img2
                    else:
                        template = img2
                        source = img1
                    
                        # Multi-scale template matching
                    scales = [1.0, 0.8, 1.2]  # Try different scales
                    for scale in scales:
                        if scale != 1.0:
                            new_width = int(template.shape[1] * scale)
                            new_height = int(template.shape[0] * scale)
                            if (new_width > 0 and new_height > 0 and 
                                new_width <= source.shape[1] and new_height <= source.shape[0]):
                                scaled_template = cv2.resize(template, (new_width, new_height))
                            else:
                                continue
                        else:
                            scaled_template = template
                        
                        # Skip if template is larger than source
                        if (scaled_template.shape[0] > source.shape[0] or 
                            scaled_template.shape[1] > source.shape[1]):
                            continue
                            
                        result = cv2.matchTemplate(source, scaled_template, method)
                        _, score, _, _ = cv2.minMaxLoc(result)
                        max_score = max(max_score, score)
                        
            except Exception as method_error:
                logger.debug(f"Template matching method {method} failed: {method_error}")
                continue
        
        logger.debug(f"Template matching score: {max_score:.3f}")
        return max(0.0, min(1.0, max_score))
        
    except Exception as e:
        logger.error(f"Error in template matching: {e}")
        return 0.0


def calculate_edge_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calculate similarity using edge detection and comparison.
    This can help identify similar shapes and structures in cards.
    
    Args:
        img1: First image as numpy array (grayscale)
        img2: Second image as numpy array (grayscale)
        
    Returns:
        float: Edge similarity score (0-1 range)
    """
    try:
        # Apply Gaussian blur to reduce noise
        blurred1 = cv2.GaussianBlur(img1, (5, 5), 0)
        blurred2 = cv2.GaussianBlur(img2, (5, 5), 0)
        
        # Apply Canny edge detection
        edges1 = cv2.Canny(blurred1, 50, 150)
        edges2 = cv2.Canny(blurred2, 50, 150)
        
        # Calculate edge density similarity
        edge_density1 = np.sum(edges1 > 0) / edges1.size
        edge_density2 = np.sum(edges2 > 0) / edges2.size
        
        # Compare edge densities
        max_density = max(edge_density1, edge_density2, 0.01)
        density_similarity = 1.0 - abs(edge_density1 - edge_density2) / max_density
        
        # Calculate structural similarity of edge maps
        edge_ssim = ssim(edges1, edges2, data_range=255)
        edge_ssim_normalized = max(0, (edge_ssim + 1) / 2)
        
        # Combine density and structural similarity
        edge_score = 0.4 * density_similarity + 0.6 * edge_ssim_normalized
        
        logger.debug(f"Edge similarity: density={density_similarity:.3f}, "
                    f"ssim={edge_ssim_normalized:.3f}, combined={edge_score:.3f}")
        return max(0.0, min(1.0, edge_score))
        
    except Exception as e:
        logger.error(f"Error in edge similarity calculation: {e}")
        return 0.0


def calculate_image_similarity(
    image_path_or_bytes1: str | bytes, 
    url_or_bytes2: str | bytes,
    resize_dim: Tuple[int, int] = (512, 512)  # Larger size for better feature detection
) -> float:
    """
    Calculate similarity score between two images.
    
    Args:
        image_path_or_bytes1: Path or bytes of the first image (user uploaded)
        url_or_bytes2: URL or bytes of the second image (card from db)
        resize_dim: Dimensions to resize images to before comparison
        
    Returns:
        Similarity score between 0 and 1 where 1 is identical
    """
    try:
        # Handle the first image (path, URL, or bytes)
        if isinstance(image_path_or_bytes1, str):
            if image_path_or_bytes1.startswith('http'):
                # It's a URL
                image_bytes1 = download_image(image_path_or_bytes1)
                if not image_bytes1:
                    return 0.0
            else:
                # It's a file path
                try:
                    with open(image_path_or_bytes1, 'rb') as f:
                        image_bytes1 = f.read()
                except Exception as e:
                    logger.error(f"Error reading image from {image_path_or_bytes1}: {str(e)}")
                    return 0.0
        else:
            image_bytes1 = image_path_or_bytes1
            
        # Handle the second image (url, path, or bytes)
        if isinstance(url_or_bytes2, str):
            if url_or_bytes2.startswith('http'):
                # It's a URL
                image_bytes2 = download_image(url_or_bytes2)
                if not image_bytes2:
                    return 0.0
            else:
                # It's a file path
                try:
                    with open(url_or_bytes2, 'rb') as f:
                        image_bytes2 = f.read()
                except Exception as e:
                    logger.error(f"Error reading image from {url_or_bytes2}: {str(e)}")
                    return 0.0
        else:
            image_bytes2 = url_or_bytes2
            
        # Open images
        img1 = Image.open(io.BytesIO(image_bytes1)).convert('RGB')
        img2 = Image.open(io.BytesIO(image_bytes2)).convert('RGB')
        
        # Resize both images to the same dimensions for fair comparison
        img1 = img1.resize(resize_dim)
        img2 = img2.resize(resize_dim)
        
        # Convert to numpy arrays for processing
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Method 1: Feature-based similarity (best for photo vs digital image)
        feature_score = calculate_feature_similarity(arr1, arr2)
        
        # Method 2: Histogram similarity (color distribution)
        histogram_score = calculate_histogram_similarity(arr1, arr2)
        
        # Method 3: Traditional SSIM (structural similarity)
        # Convert to grayscale for SSIM calculation
        gray1 = np.array(img1.convert('L'))
        gray2 = np.array(img2.convert('L'))
        
        # Calculate SSIM
        ssim_score = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
        # Normalize SSIM to 0-1 range
        ssim_normalized = max(0, (ssim_score + 1) / 2)
        
        # Method 4: Template matching score
        template_score = calculate_template_matching(gray1, gray2)
        
        # Method 5: Edge detection similarity
        edge_score = calculate_edge_similarity(gray1, gray2)
        
        # Combine all methods with weights optimized for card photo matching
        # Feature matching is most important for photos vs digital images
        combined_similarity = (
            0.40 * feature_score +     # Highest weight - best for different image types
            0.20 * histogram_score +   # Color distribution similarity
            0.15 * template_score +    # Template matching
            0.15 * edge_score +        # Edge/structure similarity
            0.10 * ssim_normalized     # Traditional SSIM
        )
        
        print(f"Image similarity: Feature={feature_score:.4f}, Histogram={histogram_score:.4f}, "
              f"SSIM={ssim_score:.4f}, Template={template_score:.4f}, "
              f"Edge={edge_score:.4f}, Combined={combined_similarity:.4f}")
        
        return max(0.0, min(1.0, combined_similarity))
    except Exception as e:
        logger.error(f"Error comparing images: {str(e)}")
        return 0.0
