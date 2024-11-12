import tkinter as tk
from PIL import Image, ImageTk
import os

# Load the Rekordbox image
image_path = 'rekordbox.png'
image = Image.open(image_path)

# Output folder for selected regions
output_folder = 'selected_boxes'
os.makedirs(output_folder, exist_ok=True)
regions_file = "regions.txt"  # Use .txt format

class BoxSelectorApp:
    def __init__(self, root, image):
        self.root = root
        self.image = image
        self.tk_image = ImageTk.PhotoImage(image)
        
        # Frame to hold the canvas and scrollbar
        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for image with scrollbar
        self.canvas = tk.Canvas(frame, width=image.width, height=min(700, image.height))
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        
        # Scrollbar setup
        self.scroll_y = tk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # List to store boxes and control panels
        self.boxes = []
        self.current_box = None
        self.selected_box_idx = None

        # Bind mouse events for box selection
        self.canvas.bind("<ButtonPress-1>", self.start_box)
        self.canvas.bind("<B1-Motion>", self.draw_box)
        self.canvas.bind("<ButtonRelease-1>", self.finish_box)
        
        # Control frame at bottom of window
        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack(side=tk.BOTTOM, pady=10)
        
        # Buttons in the control frame
        self.duplicate_button = tk.Button(self.controls_frame, text="Duplicate Box", command=self.duplicate_box)
        self.duplicate_button.grid(row=0, column=1, padx=5)
        
        self.mirror_button = tk.Button(self.controls_frame, text="Mirror Box", command=self.mirror_box)
        self.mirror_button.grid(row=0, column=2, padx=5)
        
        self.delete_button = tk.Button(self.controls_frame, text="Delete Box", command=self.delete_box)
        self.delete_button.grid(row=0, column=3, padx=5)

        # Arrow buttons for position adjustments
        self.arrow_frame = tk.Frame(self.controls_frame)
        self.arrow_frame.grid(row=0, column=4, padx=5)
        tk.Button(self.arrow_frame, text="⬆", command=lambda: self.adjust_box("up")).grid(row=0, column=1)
        tk.Button(self.arrow_frame, text="⬇", command=lambda: self.adjust_box("down")).grid(row=2, column=1)
        tk.Button(self.arrow_frame, text="⬅", command=lambda: self.adjust_box("left")).grid(row=1, column=0)
        tk.Button(self.arrow_frame, text="➡", command=lambda: self.adjust_box("right")).grid(row=1, column=2)

        # Load and save buttons
        self.save_button = tk.Button(self.controls_frame, text="Save Boxes", command=self.save_boxes)
        self.save_button.grid(row=0, column=5, padx=5)
        
        self.load_button = tk.Button(self.controls_frame, text="Load Boxes", command=self.load_boxes)
        self.load_button.grid(row=0, column=6, padx=5)
        
        # Position and size display
        self.position_label = tk.Label(self.controls_frame, text="Pos: (x, y), Size: (width x height)")
        self.position_label.grid(row=0, column=0, padx=5)

    def start_box(self, event):
        # Record the starting coordinates
        self.start_x, self.start_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        # Create a new semi-transparent red box
        self.current_box = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", fill="red", stipple="gray50", width=2
        )

    def draw_box(self, event):
        # Update the box as the mouse is dragged
        current_x, current_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.current_box, self.start_x, self.start_y, current_x, current_y)

    def finish_box(self, event):
        # Finalize the box position and save coordinates
        x1, y1, x2, y2 = self.canvas.coords(self.current_box)
        box_info = {
            "x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2), "id": self.current_box
        }
        self.boxes.append(box_info)
        self.selected_box_idx = len(self.boxes) - 1
        self.update_position_label()

    def adjust_box(self, direction):
        if self.selected_box_idx is not None:
            box = self.boxes[self.selected_box_idx]
            dx, dy = (0, -1) if direction == "up" else (0, 1) if direction == "down" else (-1, 0) if direction == "left" else (1, 0)
            self.canvas.move(box["id"], dx, dy)
            box["x1"] += dx
            box["y1"] += dy
            box["x2"] += dx
            box["y2"] += dy
            self.update_position_label()

    def duplicate_box(self):
        if self.selected_box_idx is not None:
            box = self.boxes[self.selected_box_idx]
            new_id = self.canvas.create_rectangle(
                box["x1"] + 10, box["y1"] + 10, box["x2"] + 10, box["y2"] + 10,
                outline="red", fill="red", stipple="gray50", width=2
            )
            self.boxes.append({
                "x1": box["x1"] + 10, "y1": box["y1"] + 10, "x2": box["x2"] + 10, "y2": box["y2"] + 10, "id": new_id
            })
            self.selected_box_idx = len(self.boxes) - 1
            self.update_position_label()

    def mirror_box(self):
        if self.selected_box_idx is not None:
            box = self.boxes[self.selected_box_idx]
            center_x = (box["x1"] + box["x2"]) // 2
            new_x1 = 2 * center_x - box["x2"]
            new_x2 = 2 * center_x - box["x1"]
            new_id = self.canvas.create_rectangle(
                new_x1, box["y1"], new_x2, box["y2"],
                outline="red", fill="red", stipple="gray50", width=2
            )
            self.boxes.append({
                "x1": new_x1, "y1": box["y1"], "x2": new_x2, "y2": box["y2"], "id": new_id
            })
            self.selected_box_idx = len(self.boxes) - 1
            self.update_position_label()

    def delete_box(self):
        if self.selected_box_idx is not None:
            box = self.boxes.pop(self.selected_box_idx)
            self.canvas.delete(box["id"])
            self.selected_box_idx = None if not self.boxes else len(self.boxes) - 1
            self.update_position_label()

    def save_boxes(self):
        with open(regions_file, "w") as f:
            for box in self.boxes:
                f.write(f"{box['x1']},{box['y1']},{box['x2']},{box['y2']}\n")
        print("Boxes saved to", regions_file)

    def load_boxes(self):
        if os.path.exists(regions_file):
            with open(regions_file, "r") as f:
                for line in f:
                    x1, y1, x2, y2 = map(int, line.strip().split(","))
                    box_id = self.canvas.create_rectangle(
                        x1, y1, x2, y2, outline="red", fill="red", stipple="gray50", width=2
                    )
                    self.boxes.append({
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2, "id": box_id
                    })
            self.update_position_label()
            print("Boxes loaded from", regions_file)

    def update_position_label(self):
        if self.selected_box_idx is not None:
            box = self.boxes[self.selected_box_idx]
            self.position_label.config(text=f"Pos: ({box['x1']}, {box['y1']}), Size: ({box['x2']-box['x1']}x{box['y2']-box['y1']})")
        else:
            self.position_label.config(text="Pos: (x, y), Size: (width x height)")

# Initialize and run the app
root = tk.Tk()
root.title("Rekordbox Box Selector")
app = BoxSelectorApp(root, image)
root.mainloop()
