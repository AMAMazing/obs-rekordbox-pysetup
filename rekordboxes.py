import os
import time
import cv2
import numpy as np
from obswebsocket import obsws, requests, exceptions
from dotenv import load_dotenv
from skimage.metrics import structural_similarity as ssim
from PIL import Image

# Load environment variables from .env file
load_dotenv()

# OBS connection details
host = "localhost"
port = 4455
password = os.getenv("OBS_PASSWORD")

# Settings
scene_name = "DJing"  # Name of your OBS scene
rekordbox_source_names = ["Rekordbox Capture 1", "Rekordbox Capture 2"]  # Add more if needed
max_iterations = 20
similarity_threshold = 0.99  # Desired similarity (1.0 is identical)
adjustment_step = 5  # Pixels to adjust per iteration

# Paths
target_image_path = "rekordbox.png"  # Image with the selected boxes

# Load target image
target_image = cv2.imread(target_image_path)

# Check if target image is loaded
if target_image is None:
    print(f"Failed to load target image from {target_image_path}")
    exit(1)

# Convert target image to RGB
target_image = cv2.cvtColor(target_image, cv2.COLOR_BGR2RGB)

# Initialize OBS WebSocket
ws = obsws(host, port, password)

try:
    ws.connect()
    print("Connected to OBS WebSocket")

    # Get canvas size
    video_info = ws.call(requests.GetVideoInfo())
    canvas_width = video_info.getBaseWidth()
    canvas_height = video_info.getBaseHeight()

    # Step 1: Set Rekordbox sources to fit screen centered
    for source_name in rekordbox_source_names:
        # Get scene item ID
        scene_item = ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        scene_item_id = scene_item.getSceneItemId()

        # Reset transform: position at center, scale 1:1, no crop
        ws.call(requests.SetSceneItemTransform(
            sceneName=scene_name,
            sceneItemId=scene_item_id,
            sceneItemTransform={
                "positionX": canvas_width / 2,
                "positionY": canvas_height / 2,
                "rotation": 0.0,
                "scaleX": 1.0,
                "scaleY": 1.0,
                "cropLeft": 0,
                "cropRight": 0,
                "cropTop": 0,
                "cropBottom": 0,
                "alignment": 5  # Center alignment
            }
        ))

    # Iteratively adjust transforms
    for iteration in range(max_iterations):
        print(f"\nIteration {iteration + 1}/{max_iterations}")

        # Capture OBS output
        screenshot_response = ws.call(requests.GetSourceScreenshot(
            sourceName="Program",
            embedPictureFormat="png",
            width=canvas_width,
            height=canvas_height
        ))
        img_data_base64 = screenshot_response.getImageData()
        img_data = base64.b64decode(img_data_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        obs_output_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        obs_output_image = cv2.cvtColor(obs_output_image, cv2.COLOR_BGR2RGB)

        # Compare OBS output to target image
        similarity = compare_images(target_image, obs_output_image)
        print(f"Similarity: {similarity:.4f}")

        if similarity >= similarity_threshold:
            print("Desired similarity achieved.")
            break

        # Adjust transforms based on comparison
        adjust_transforms(ws, scene_name, rekordbox_source_names, target_image, obs_output_image, adjustment_step)

        # Wait a moment for OBS to update
        time.sleep(0.5)

except exceptions.ConnectionFailure:
    print("Failed to connect to OBS WebSocket. Check if OBS is open and WebSocket server is enabled.")

finally:
    try:
        ws.disconnect()
        print("Disconnected from OBS WebSocket")
    except AttributeError:
        print("No active WebSocket connection to close.")

def compare_images(img1, img2):
    """
    Compare two images using Structural Similarity Index (SSIM).
    Returns a similarity score between 0 and 1.
    """
    # Resize images to the same size
    height = min(img1.shape[0], img2.shape[0])
    width = min(img1.shape[1], img2.shape[1])
    img1_resized = cv2.resize(img1, (width, height))
    img2_resized = cv2.resize(img2, (width, height))

    # Convert to grayscale
    img1_gray = cv2.cvtColor(img1_resized, cv2.COLOR_RGB2GRAY)
    img2_gray = cv2.cvtColor(img2_resized, cv2.COLOR_RGB2GRAY)

    # Compute SSIM
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

def adjust_transforms(ws, scene_name, source_names, target_image, obs_image, step):
    """
    Adjust the transforms of Rekordbox sources in OBS based on image comparison.
    """
    # Calculate difference image
    diff_image = cv2.absdiff(target_image, obs_image)
    diff_gray = cv2.cvtColor(diff_image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(diff_gray, 50, 255, cv2.THRESH_BINARY)
    moments = cv2.moments(thresh)

    if moments["m00"] == 0:
        print("No difference detected.")
        return

    # Calculate centroid of the difference
    cX = int(moments["m10"] / moments["m00"])
    cY = int(moments["m01"] / moments["m00"])
    print(f"Difference centroid at: ({cX}, {cY})")

    # For each Rekordbox source, adjust the position and scale
    for source_name in source_names:
        # Get scene item ID
        scene_item = ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        scene_item_id = scene_item.getSceneItemId()

        # Get current transform
        transform_response = ws.call(requests.GetSceneItemTransform(
            sceneName=scene_name,
            sceneItemId=scene_item_id
        ))
        transform = transform_response.getSceneItemTransform()

        # Adjust position
        new_positionX = transform['positionX'] - step if cX > canvas_width / 2 else transform['positionX'] + step
        new_positionY = transform['positionY'] - step if cY > canvas_height / 2 else transform['positionY'] + step

        # Adjust scale
        new_scaleX = transform['scaleX'] + (step / 100) if moments['mu20'] > moments['mu02'] else transform['scaleX'] - (step / 100)
        new_scaleY = transform['scaleY'] + (step / 100) if moments['mu02'] > moments['mu20'] else transform['scaleY'] - (step / 100)

        # Set new transform
        ws.call(requests.SetSceneItemTransform(
            sceneName=scene_name,
            sceneItemId=scene_item_id,
            sceneItemTransform={
                "positionX": new_positionX,
                "positionY": new_positionY,
                "rotation": transform['rotation'],
                "scaleX": new_scaleX,
                "scaleY": new_scaleY,
                "cropLeft": transform['cropLeft'],
                "cropRight": transform['cropRight'],
                "cropTop": transform['cropTop'],
                "cropBottom": transform['cropBottom'],
                "alignment": transform['alignment']
            }
        ))

        print(f"Adjusted '{source_name}': Position ({new_positionX}, {new_positionY}), Scale ({new_scaleX}, {new_scaleY})")
