import tkinter as tk
from PIL import Image, ImageTk

class AutoBorderBoxTool:
    def __init__(self, root, image_path):
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
        self.boundary_color = (30, 30, 30)  # Set a default boundary color
        self.folder = "selected_boxes"
        
        self.canvas.bind("<Button-1>", self.set_start_point)
        
        # Create save button
        save_button = tk.Button(root, text="Save Boxes", command=self.save_boxes)
        save_button.pack()

    def set_start_point(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.expand_box()

    def expand_box(self):
        x, y = self.start_x, self.start_y
        width, height = self.image.size
        pixels = self.image.load()

        # Initialize box boundaries
        left, right, top, bottom = x, x, y, y

        # Expand to the right
        while right < width and pixels[right, y][:3] != self.boundary_color:
            right += 1

        # Expand to the bottom
        while bottom < height and pixels[x, bottom][:3] != self.boundary_color:
            bottom += 1

        # Expand to the left
        while left > 0 and pixels[left, y][:3] != self.boundary_color:
            left -= 1

        # Expand to the top
        while top > 0 and pixels[x, top][:3] != self.boundary_color:
            top -= 1

        # Draw the box
        if self.box:
            self.canvas.delete(self.box)
        self.box = self.canvas.create_rectangle(left, top, right, bottom, outline="red")

        # Store the box coordinates
        self.box_coords = (left, top, right, bottom)

    def save_boxes(self):
        if self.box_coords:
            # Create the folder if it doesn't exist
            os.makedirs(self.folder, exist_ok=True)
            # Crop the image to the bounding box
            cropped_image = self.image.crop(self.box_coords)
            # Save the cropped image
            cropped_image.save(f"{self.folder}/box_{self.start_x}_{self.start_y}.png")
            print(f"Box saved as box_{self.start_x}_{self.start_y}.png")

if __name__ == "__main__":
    import os
    root = tk.Tk()
    app = AutoBorderBoxTool(root, "rekordbox.png")
    root.mainloop()
