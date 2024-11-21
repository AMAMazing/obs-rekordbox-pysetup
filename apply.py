import os
import base64
from obswebsocket import obsws, requests
from PIL import Image
import json
from pathlib import Path
import io

class RekordboxTransformAutomator:
    def __init__(self, host="localhost", port=4455, password=None):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.scene_name = "DJing"
        self.template_folder = "selected_boxes"
        self.templates = {}
        self.source_screenshot = None
        
    def connect_obs(self):
        """Establish connection to OBS WebSocket."""
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            print("Connected to OBS WebSocket")
            return True
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            return False

    def load_templates(self):
        """Load saved template boxes from the selected_boxes folder."""
        if not os.path.exists(self.template_folder):
            print(f"Template folder '{self.template_folder}' not found")
            return False
            
        for file in os.listdir(self.template_folder):
            if file.endswith('.png'):
                template_img = Image.open(os.path.join(self.template_folder, file))
                self.templates[file] = {
                    'width': template_img.width,
                    'height': template_img.height,
                    'aspect_ratio': template_img.width / template_img.height
                }
        print(f"Loaded {len(self.templates)} templates")
        return len(self.templates) > 0

    def capture_source_screenshot(self):
        """Capture a screenshot of the current Rekordbox window."""
        try:
            # First, get all inputs to verify the capture exists
            inputs_response = self.ws.call(requests.GetInputList())
            
            # Debug print the response
            print("Available inputs:", [input.get('inputName', '') for input in inputs_response.datain.get('inputs', [])])
            
            capture_name = "Rekordbox Capture 1"
            if not any(input.get('inputName') == capture_name for input in inputs_response.datain.get('inputs', [])):
                print(f"Source '{capture_name}' not found in OBS")
                return False

            # Get source screenshot using OBS
            response = self.ws.call(requests.GetSourceScreenshot(
                sourceName=capture_name,
                imageFormat="png",
                imageWidth=1920,
                imageHeight=1080
            ))
            
            # Debug print the response
            print("Screenshot response:", response.datain)
            
            # The response contains the image data in base64 format
            img_data = response.datain.get('imageData')
            if not img_data:
                print("No image data received from OBS")
                return False

            # Remove the data URI prefix if present
            if img_data.startswith('data:image/png;base64,'):
                img_data = img_data.split(',')[1]

            # Decode base64 to bytes
            img_bytes = base64.b64decode(img_data)
            
            # Convert to PIL Image
            self.source_screenshot = Image.open(io.BytesIO(img_bytes))
            print(f"Successfully captured screenshot: {self.source_screenshot.size}")
            return True
            
        except Exception as e:
            print(f"Failed to capture screenshot: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def calculate_transforms(self):
        """Calculate the necessary transforms to match templates."""
        if not self.source_screenshot:
            print("No source screenshot available")
            return None

        source_width = self.source_screenshot.width
        source_height = self.source_screenshot.height
        print(f"Source dimensions: {source_width}x{source_height}")
        
        transforms = {}
        
        # Sort templates by size (assuming larger templates are for the main deck views)
        sorted_templates = sorted(
            self.templates.items(),
            key=lambda x: x[1]['width'] * x[1]['height'],
            reverse=True
        )
        
        # Calculate base position for center alignment
        base_x = 1920 // 2  # Assuming 1920x1080 canvas
        base_y = 1080 // 2
        
        for i, (template_name, template_data) in enumerate(sorted_templates):
            # Calculate scale to match template aspect ratio
            target_ar = template_data['aspect_ratio']
            scale = min(
                template_data['width'] / source_width,
                template_data['height'] / source_height
            )
            
            # Calculate position based on template index
            if i < 2:  # Main deck views
                x_offset = (i * 600) - 300  # Space them horizontally
                y_offset = 0
            else:  # Smaller views
                x_offset = ((i-2) * 300) - 150
                y_offset = 300
            
            source_name = f"Rekordbox Capture {i+1}"
            transforms[source_name] = {
                "positionX": base_x + x_offset,
                "positionY": base_y + y_offset,
                "rotation": 0.0,
                "scaleX": scale,
                "scaleY": scale,
                "cropLeft": 0,
                "cropRight": 0,
                "cropTop": 0,
                "cropBottom": 0,
                "sourceWidth": source_width,
                "sourceHeight": source_height,
                "width": source_width,
                "height": source_height,
                "alignment": 0
            }
            
            print(f"Calculated transform for {source_name}: scale={scale:.2f}, pos=({base_x + x_offset}, {base_y + y_offset})")
            
        return transforms

    def apply_transforms(self, transforms):
        """Apply the calculated transforms to OBS sources."""
        try:
            # Get scene items
            scene_items_response = self.ws.call(requests.GetSceneItemList(sceneName=self.scene_name))
            scene_items = scene_items_response.getSceneItems()
            
            # Apply transforms
            for item in scene_items:
                source_name = item['sourceName']
                if source_name in transforms:
                    transform = transforms[source_name]
                    try:
                        self.ws.call(requests.SetSceneItemTransform(
                            sceneName=self.scene_name,
                            sceneItemId=item['sceneItemId'],
                            sceneItemTransform=transform
                        ))
                        print(f"Successfully applied transform to '{source_name}'")
                    except Exception as e:
                        print(f"Failed to apply transform to '{source_name}': {str(e)}")
            return True
        except Exception as e:
            print(f"Failed to apply transforms: {str(e)}")
            return False

    def run(self):
        """Main execution flow."""
        try:
            if not self.connect_obs():
                return False
                
            if not self.load_templates():
                print("No templates found")
                return False
                
            if not self.capture_source_screenshot():
                return False
                
            transforms = self.calculate_transforms()
            if not transforms:
                return False
                
            success = self.apply_transforms(transforms)
            
            return success
        finally:
            if self.ws:
                self.ws.disconnect()
                print("Disconnected from OBS WebSocket")

def main():
    # Load password from environment variable
    password = os.getenv("OBS_PASSWORD")
    if not password:
        print("OBS_PASSWORD environment variable not set")
        return
    
    automator = RekordboxTransformAutomator(password=password)
    success = automator.run()
    
    if success:
        print("Successfully transformed Rekordbox captures")
    else:
        print("Failed to transform Rekordbox captures")

if __name__ == "__main__":
    main()