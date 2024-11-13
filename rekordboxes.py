import tkinter as tk
from PIL import Image, ImageTk
import os

class AutoBorderBoxTool:
    def __init__(self, root, image_path="rekordbox.png"):
        self.root = root
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.image)
        
        # Canvas setup
        self.canvas = tk.Canvas(root, width=self.image.width, height=self.image.height)
        self.canvas.pack()
        self.background_image = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        
        self.start_x = None
        self.start_y = None
        self.current_box = None
        self.second_box = None
        self.folder = "selected_boxes"
        
        # Box coordinates list
        self.box_coords_list = []
        
        # Color tolerance and steps
        self.color_tolerance = 1
        self.step_size = 1
        self.max_right_limit = 300
        
        # Create control panel window
        self.control_panel = tk.Toplevel(root)
        self.control_panel.title("Control Panel")
        self.control_panel.geometry("200x100")
        
        # Place buttons at the bottom of the control panel
        button_frame = tk.Frame(self.control_panel)
        button_frame.pack(side="bottom", fill="x", pady=5)
        
        # Save and Merge buttons
        save_button = tk.Button(button_frame, text="Save Boxes", command=self.save_boxes)
        save_button.pack(side="left", expand=True)
        merge_button = tk.Button(button_frame, text="Merge Boxes", command=self.merge_boxes)
        merge_button.pack(side="right", expand=True)
        
        # Bind mouse click to create boxes
        self.canvas.bind("<Button-1>", self.set_start_point)

    def set_start_point(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.expand_box()
        
        # Only allow two boxes to be displayed (one red, one blue)
        if len(self.box_coords_list) == 1:
            # Clear previous blue box if it exists
            if self.second_box:
                self.canvas.delete(self.second_box)
            self.second_box = self.canvas.create_rectangle(*self.box_coords, outline="blue")
        else:
            # Clear previous red box if it exists
            if self.current_box:
                self.canvas.delete(self.current_box)
            self.current_box = self.canvas.create_rectangle(*self.box_coords, outline="red")
            # Reset list to only keep two boxes
            self.box_coords_list = []

        # Store coordinates for potential merging
        self.box_coords_list.append(self.box_coords)

    def color_difference(self, color1, color2):
        """Calculate the color difference based on RGB components."""
        return sum(abs(color1[i] - color2[i]) for i in range(3))

    def expand_box(self):
        x, y = self.start_x, self.start_y
        width, height = self.image.size
        pixels = self.image.load()

        # Starting color
        start_color = pixels[x, y][:3]
        
        # Initialize box boundaries
        left, right, top, bottom = x, x, y, y

        # Expand in each direction until a color boundary is hit
        while right < width and right - x < self.max_right_limit and self.color_difference(pixels[right, y][:3], start_color) < self.color_tolerance:
            right += self.step_size

        while bottom < height and self.color_difference(pixels[x, bottom][:3], start_color) < self.color_tolerance:
            bottom += self.step_size

        while left > 0 and self.color_difference(pixels[left, y][:3], start_color) < self.color_tolerance:
            left -= self.step_size

        while top > 0 and self.color_difference(pixels[x, top][:3], start_color) < self.color_tolerance:
            top -= self.step_size

        # Update the box coordinates
        self.box_coords = [left, top, right, bottom]

    def merge_boxes(self):
        """Merge the two boxes into a single larger box."""
        if len(self.box_coords_list) < 2:
            print("Need two boxes to merge.")
            return

        # Take the two boxes
        box1 = self.box_coords_list[0]
        box2 = self.box_coords_list[1]

        # Calculate combined box coordinates
        left = min(box1[0], box2[0])
        top = min(box1[1], box2[1])
        right = max(box1[2], box2[2])
        bottom = max(box1[3], box2[3])

        # Clear individual boxes
        if self.current_box:
            self.canvas.delete(self.current_box)
        if self.second_box:
            self.canvas.delete(self.second_box)

        # Draw the merged box in green
        self.current_box = self.canvas.create_rectangle(left, top, right, bottom, outline="green")
        self.canvas.update()  # Update canvas after drawing combined box

        # Update the stored coordinates for the merged box
        self.box_coords = [left, top, right, bottom]
        self.box_coords_list = [self.box_coords]  # Reset to only the merged box

    def save_boxes(self):
        # Create the folder if it doesn't exist
        os.makedirs(self.folder, exist_ok=True)
        
        if self.box_coords:
            # Crop the image to the bounding box
            cropped_image = self.image.crop(self.box_coords)
            # Save the cropped image
            cropped_image.save(f"{self.folder}/box_{self.start_x}_{self.start_y}.png")
            print(f"Box saved as box_{self.start_x}_{self.start_y}.png")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoBorderBoxTool(root, "rekordbox.png")
    root.mainloop()
