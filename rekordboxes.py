import tkinter as tk
from PIL import Image, ImageTk
import os

class AutoBorderBoxTool:
    def __init__(self, root, image_path="rekordbox.png"):
        self.root = root
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.image)
        
        self.canvas = tk.Canvas(root, width=self.image.width, height=self.image.height)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        
        self.start_x = None
        self.start_y = None
        self.box = None
        self.folder = "selected_boxes"
        
        # Extremely low color tolerance for high sensitivity
        self.color_tolerance = 10  # Further reduced for maximum sensitivity
        self.step_size = 1  # Smaller steps for expansion
        self.max_right_limit = 300  # Example limit in pixels for right boundary expansion
        
        # Bind mouse click to set start point
        self.canvas.bind("<Button-1>", self.set_start_point)
        # Bind arrow keys for expanding over other areas manually
        self.root.bind("<KeyPress>", self.adjust_box_with_keys)
        
        # Save button
        save_button = tk.Button(root, text="Save Boxes", command=self.save_boxes)
        save_button.pack()

    def set_start_point(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.expand_box()

    def color_difference(self, color1, color2):
        """Calculate the color difference based on RGB components."""
        return sum(abs(color1[i] - color2[i]) for i in range(3))

    def expand_box(self):
        x, y = self.start_x, self.start_y
        width, height = self.image.size
        pixels = self.image.load()

        # Starting color at the clicked point
        start_color = pixels[x, y][:3]
        
        # Initialize box boundaries
        left, right, top, bottom = x, x, y, y

        # Expand in each direction until a color boundary is hit
        # Right expansion with a maximum limit
        while right < width and right - x < self.max_right_limit and self.color_difference(pixels[right, y][:3], start_color) < self.color_tolerance:
            right += self.step_size

        # Bottom expansion
        while bottom < height and self.color_difference(pixels[x, bottom][:3], start_color) < self.color_tolerance:
            bottom += self.step_size

        # Left expansion
        while left > 0 and self.color_difference(pixels[left, y][:3], start_color) < self.color_tolerance:
            left -= self.step_size

        # Top expansion
        while top > 0 and self.color_difference(pixels[x, top][:3], start_color) < self.color_tolerance:
            top -= self.step_size

        # Draw the box
        if self.box:
            self.canvas.delete(self.box)
        self.box = self.canvas.create_rectangle(left, top, right, bottom, outline="red")

        # Store the box coordinates
        self.box_coords = [left, top, right, bottom]

    def adjust_box_with_keys(self, event):
        """Allow fine-tuning the box expansion with arrow keys."""
        left, top, right, bottom = self.box_coords
        if event.keysym == "Right":
            right += 1
        elif event.keysym == "Down":
            bottom += 1
        elif event.keysym == "Left" and left > 0:
            left -= 1
        elif event.keysym == "Up" and top > 0:
            top -= 1

        # Redraw the adjusted box
        self.canvas.delete(self.box)
        self.box = self.canvas.create_rectangle(left, top, right, bottom, outline="red")
        self.box_coords = [left, top, right, bottom]

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
