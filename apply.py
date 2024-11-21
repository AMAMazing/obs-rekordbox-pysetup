import cv2
import numpy as np
import os
from obswebsocket import obsws, requests, exceptions
from time import sleep

# OBS WebSocket Connection Settings
host = "localhost"
port = 4455
password = os.getenv("OBS_PASSWORD")  # Set OBS_PASSWORD in your environment variables

# OBS Screenshot and Adjustment Functionality
class OBSAdjuster:
    def __init__(self, host, port, password):
        self.ws = obsws(host, port, password)
        self.scene_name = "DJing"

    def connect(self):
        try:
            self.ws.connect()
            print("Connected to OBS WebSocket")
        except exceptions.ConnectionFailure:
            raise Exception("Failed to connect to OBS WebSocket. Ensure OBS is running and the WebSocket server is enabled.")

    def disconnect(self):
        self.ws.disconnect()
        print("Disconnected from OBS WebSocket")

    def take_screenshot(self, file_path):
        """Take a screenshot of the current scene."""
        try:
            response = self.ws.call(requests.TakeSourceScreenshot(
                sourceName=self.scene_name,
                embedPictureFormat="png",
                saveToFilePath=file_path
            ))
            print(f"Screenshot saved to: {file_path}")
        except Exception as e:
            raise Exception(f"Failed to take screenshot: {e}")

    def adjust_source(self, source_name, transform):
        """Adjust a source in the OBS scene."""
        try:
            scene_items = self.ws.call(requests.GetSceneItemList(sceneName=self.scene_name)).getSceneItems()
            source_id = next(item["sceneItemId"] for item in scene_items if item["sourceName"] == source_name)

            self.ws.call(requests.SetSceneItemTransform(
                sceneName=self.scene_name,
                sceneItemId=source_id,
                sceneItemTransform=transform
            ))
            print(f"Adjusted source: {source_name}")
        except StopIteration:
            raise Exception(f"Source '{source_name}' not found in scene '{self.scene_name}'.")
        except Exception as e:
            raise Exception(f"Failed to adjust source: {e}")

    def iteratively_adjust(self, sources, screenshot_path="obs_screenshot.png"):
        """
        Iteratively adjust the layout based on screenshots until the layout is perfect.
        """
        for i in range(5):  # Limit iterations to avoid infinite loops
            print(f"Iteration {i + 1}: Taking a screenshot and adjusting layout...")
            
            # Take a screenshot of the current scene
            self.take_screenshot(screenshot_path)

            # Analyze the screenshot
            image = cv2.imread(screenshot_path)
            if image is None:
                raise Exception(f"Failed to load screenshot: {screenshot_path}")

            # Perform analysis or adjustments (e.g., detect misalignment and adjust)
            # Here we just simulate adjustments
            for source_name, transform in sources.items():
                # Adjust each source slightly for demonstration
                transform["positionX"] += 10  # Example adjustment
                transform["positionY"] += 10  # Example adjustment
                self.adjust_source(source_name, transform)

            # Simulate a stopping condition based on analysis
            # For example, you could use OpenCV to detect misaligned regions
            # Here we stop after 5 iterations
            print("Adjustment complete for this iteration.")

        print("Finished iterative adjustments.")

# Example Usage
def main():
    obs_adjuster = OBSAdjuster(host, port, password)

    # Example transforms for sources (customize for your layout)
    sources = {
        "Rekordbox Capture 1": {
            "positionX": 300.0,
            "positionY": 200.0,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "rotation": 0.0,
            "cropLeft": 0,
            "cropRight": 0,
            "cropTop": 0,
            "cropBottom": 0
        },
        "Rekordbox Capture 2": {
            "positionX": 600.0,
            "positionY": 400.0,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "rotation": 0.0,
            "cropLeft": 0,
            "cropRight": 0,
            "cropTop": 0,
            "cropBottom": 0
        }
    }

    try:
        # Connect to OBS
        obs_adjuster.connect()

        # Iteratively adjust the layout
        obs_adjuster.iteratively_adjust(sources)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        obs_adjuster.disconnect()

if __name__ == "__main__":
    main()
