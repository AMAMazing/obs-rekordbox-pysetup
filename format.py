import sys
import re
from PyQt5 import QtCore, QtGui, QtWidgets

class ImageItem(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pixmap, index):
        super().__init__(pixmap)
        self.index = index
        self.setAcceptHoverEvents(True)
        self.default_opacity = 1.0
        self.hover_opacity = 0.6
        self.original_pixmap = pixmap.copy()

    def hoverEnterEvent(self, event):
        self.setOpacity(self.hover_opacity)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setOpacity(self.default_opacity)
        super().hoverLeaveEvent(event)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, image_paths):
        super().__init__()
        self.setWindowTitle("Advanced Image Manipulation GUI")
        self.image_paths = image_paths
        self.images = []
        self.selected_image_index = None
        self.command_history = []
        self.init_ui()

    def init_ui(self):
        # Create the graphics view and scene
        self.graphics_view = QtWidgets.QGraphicsView()
        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        # Set scene size
        scene_width = 800
        scene_height = int(scene_width * 9 / 16)
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
        self.graphics_view.setFixedSize(scene_width + 2, scene_height + 2)
        self.graphics_view.setAlignment(QtCore.Qt.AlignCenter)

        # Load images
        self.load_images()

        # Create control panel
        self.create_control_panel()

        # Create command list view
        self.create_command_list_view()

        # Set layout
        main_layout = QtWidgets.QHBoxLayout()

        # Left side: graphics view
        main_layout.addWidget(self.graphics_view)

        # Right side: command list and controls
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.command_list_widget)
        right_layout.addWidget(self.import_export_widget)
        right_layout.addWidget(self.control_panel)
        right_layout.addWidget(self.image_selector)

        right_container = QtWidgets.QWidget()
        right_container.setLayout(right_layout)

        main_layout.addWidget(right_container)

        container = QtWidgets.QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_images(self):
        num_images = len(self.image_paths)
        scene_width = self.scene.width()
        scene_height = self.scene.height()

        # Decide on grid dimensions
        cols = int(num_images ** 0.5)
        rows = (num_images + cols - 1) // cols  # Ceiling division

        # Compute cell size
        cell_width = scene_width / cols
        cell_height = scene_height / rows

        for idx, path in enumerate(self.image_paths):
            pixmap = QtGui.QPixmap(path)
            # Scale images to fit within cell size
            pixmap = pixmap.scaled(int(cell_width * 0.8),
                                   int(cell_height * 0.8),
                                   QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            image_item = ImageItem(pixmap, idx)
            image_item.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable)

            # Compute position
            col = idx % cols
            row = idx // cols
            x = col * cell_width + (cell_width - pixmap.width()) / 2
            y = row * cell_height + (cell_height - pixmap.height()) / 2
            image_item.setPos(x, y)
            self.scene.addItem(image_item)
            self.images.append(image_item)

        # Set the first image as selected by default
        if self.images:
            self.selected_image_index = 0
            self.images[0].setSelected(True)

    def reset_images(self):
        self.scene.clear()
        self.images = []
        self.selected_image_index = None
        self.load_images()

    def create_control_panel(self):
        # Image Selector Buttons
        self.image_selector = QtWidgets.QWidget()
        selector_layout = QtWidgets.QHBoxLayout()
        selector_label = QtWidgets.QLabel("Select Image:")
        selector_layout.addWidget(selector_label)

        for idx in range(len(self.image_paths)):
            btn = QtWidgets.QPushButton(f"Image {idx + 1}")
            btn.clicked.connect(lambda _, i=idx: self.select_image(i))
            selector_layout.addWidget(btn)

        self.image_selector.setLayout(selector_layout)

        # Control Panel for selected image
        self.control_panel = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()

        # Rotate button
        rotate_btn = QtWidgets.QPushButton("Rotate Image")
        rotate_btn.clicked.connect(lambda: self.rotate_image())
        layout.addWidget(rotate_btn, 0, 0)

        # Scale buttons
        scale_vert_btn = QtWidgets.QPushButton("Scale Vertically")
        scale_vert_btn.clicked.connect(lambda: self.scale_image(fit_vertical=True))
        layout.addWidget(scale_vert_btn, 0, 1)

        scale_horiz_btn = QtWidgets.QPushButton("Scale Horizontally")
        scale_horiz_btn.clicked.connect(lambda: self.scale_image(fit_vertical=False))
        layout.addWidget(scale_horiz_btn, 0, 2)

        # Custom scale button
        custom_scale_btn = QtWidgets.QPushButton("Custom Scale")
        custom_scale_btn.clicked.connect(lambda: self.custom_scale_image())
        layout.addWidget(custom_scale_btn, 0, 3)

        # Scale down button
        scale_down_btn = QtWidgets.QPushButton("Scale Down")
        scale_down_btn.clicked.connect(self.scale_down_image)
        layout.addWidget(scale_down_btn, 0, 4)

        # Crop button
        crop_btn = QtWidgets.QPushButton("Crop Image")
        crop_btn.clicked.connect(self.crop_image)
        layout.addWidget(crop_btn, 0, 5)

        # Reset Crop button
        reset_crop_btn = QtWidgets.QPushButton("Reset Crop")
        reset_crop_btn.clicked.connect(self.reset_crop_image)
        layout.addWidget(reset_crop_btn, 0, 6)

        # Movement buttons
        move_left_btn = QtWidgets.QPushButton("Move Left")
        move_left_btn.clicked.connect(lambda: self.move_image(-20, 0))
        layout.addWidget(move_left_btn, 1, 0)

        move_right_btn = QtWidgets.QPushButton("Move Right")
        move_right_btn.clicked.connect(lambda: self.move_image(20, 0))
        layout.addWidget(move_right_btn, 1, 1)

        move_up_btn = QtWidgets.QPushButton("Move Up")
        move_up_btn.clicked.connect(lambda: self.move_image(0, -20))
        layout.addWidget(move_up_btn, 1, 2)

        move_down_btn = QtWidgets.QPushButton("Move Down")
        move_down_btn.clicked.connect(lambda: self.move_image(0, 20))
        layout.addWidget(move_down_btn, 1, 3)

        # Centering buttons
        center_horiz_btn = QtWidgets.QPushButton("Center Horizontally")
        center_horiz_btn.clicked.connect(self.center_image_horizontally)
        layout.addWidget(center_horiz_btn, 2, 0)

        center_vert_btn = QtWidgets.QPushButton("Center Vertically")
        center_vert_btn.clicked.connect(self.center_image_vertically)
        layout.addWidget(center_vert_btn, 2, 1)

        # Snap to canvas button
        snap_to_canvas_btn = QtWidgets.QPushButton("Snap to Canvas")
        snap_to_canvas_btn.clicked.connect(lambda: self.snap_to_canvas())
        layout.addWidget(snap_to_canvas_btn, 2, 2)

        # Snap to image button
        snap_to_image_btn = QtWidgets.QPushButton("Snap to Image")
        snap_to_image_btn.clicked.connect(lambda: self.snap_to_image())
        layout.addWidget(snap_to_image_btn, 2, 3)

        self.control_panel.setLayout(layout)

    def create_command_list_view(self):
        self.command_list_widget = QtWidgets.QListWidget()
        self.command_list_widget.setMinimumWidth(200)

        # Import and Export buttons
        self.import_export_widget = QtWidgets.QWidget()
        import_export_layout = QtWidgets.QHBoxLayout()
        import_btn = QtWidgets.QPushButton("Import Commands")
        import_btn.clicked.connect(self.import_commands)
        export_btn = QtWidgets.QPushButton("Export Commands")
        export_btn.clicked.connect(self.export_commands)
        import_export_layout.addWidget(import_btn)
        import_export_layout.addWidget(export_btn)
        self.import_export_widget.setLayout(import_export_layout)

    def select_image(self, index):
        # Deselect previous image
        if self.selected_image_index is not None:
            self.images[self.selected_image_index].setSelected(False)
        # Select new image
        self.selected_image_index = index
        self.images[index].setSelected(True)
        self.log_command(f"Selected Image {index + 1}")

    def get_selected_image(self):
        if self.selected_image_index is not None:
            return self.images[self.selected_image_index]
        else:
            QtWidgets.QMessageBox.warning(self, "No Image Selected", "Please select an image to manipulate.")
            return None

    def rotate_image(self, angle=90, *args):
        image_item = self.get_selected_image()
        if image_item:
            pixmap = image_item.pixmap().transformed(QtGui.QTransform().rotate(angle), QtCore.Qt.SmoothTransformation)
            image_item.setPixmap(pixmap)
            self.log_command(f"Rotated Image {self.selected_image_index + 1} by {angle} degrees")

    def scale_image(self, fit_vertical=False):
        image_item = self.get_selected_image()
        if image_item:
            scene_rect = self.scene.sceneRect()
            if fit_vertical:
                new_height = int(scene_rect.height())
                pixmap = image_item.pixmap().scaledToHeight(new_height, QtCore.Qt.SmoothTransformation)
                self.log_command(f"Scaled Image {self.selected_image_index + 1} to fit scene height")
            else:
                new_width = int(scene_rect.width())
                pixmap = image_item.pixmap().scaledToWidth(new_width, QtCore.Qt.SmoothTransformation)
                self.log_command(f"Scaled Image {self.selected_image_index + 1} to fit scene width")
            image_item.setPixmap(pixmap)
            self.center_image()

    def custom_scale_image(self, choice=None, scale_factor=None, width=None, height=None):
        image_item = self.get_selected_image()
        if image_item:
            if choice is None:
                choice, ok = QtWidgets.QInputDialog.getItem(
                    self, "Custom Scaling", "Choose scaling method:", ["Scale Factor", "Set Dimensions"], 0, False)
                if not ok or not choice:
                    return
            if choice == "Scale Factor":
                if scale_factor is None:
                    scale_factor, ok = QtWidgets.QInputDialog.getDouble(
                        self, "Scale Factor", "Enter scale factor:", 1.0, 0.1, 10.0, 2)
                    if not ok:
                        return
                pixmap = image_item.pixmap()
                new_width = int(pixmap.width() * scale_factor)
                new_height = int(pixmap.height() * scale_factor)
                pixmap = pixmap.scaled(new_width, new_height, QtCore.Qt.KeepAspectRatio,
                                       QtCore.Qt.SmoothTransformation)
                image_item.setPixmap(pixmap)
                self.center_image()
                self.log_command(f"Scaled Image {self.selected_image_index + 1} by factor {scale_factor}")
            elif choice == "Set Dimensions":
                if width is None or height is None:
                    width, ok_w = QtWidgets.QInputDialog.getInt(
                        self, "Set Width", "Enter new width:", value=image_item.pixmap().width(), min=1)
                    height, ok_h = QtWidgets.QInputDialog.getInt(
                        self, "Set Height", "Enter new height:", value=image_item.pixmap().height(), min=1)
                    if not (ok_w and ok_h):
                        return
                pixmap = image_item.pixmap().scaled(width, height, QtCore.Qt.IgnoreAspectRatio,
                                                    QtCore.Qt.SmoothTransformation)
                image_item.setPixmap(pixmap)
                self.center_image()
                self.log_command(f"Set dimensions of Image {self.selected_image_index + 1} to {width}x{height}")

    def scale_down_image(self):
        image_item = self.get_selected_image()
        if image_item:
            scale_factor = 0.8
            pixmap = image_item.pixmap()
            new_width = int(pixmap.width() * scale_factor)
            new_height = int(pixmap.height() * scale_factor)
            pixmap = pixmap.scaled(new_width, new_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            image_item.setPixmap(pixmap)
            self.center_image()
            self.log_command(f"Scaled down Image {self.selected_image_index + 1} by 20%")

    def crop_image(self, side=None, crop_amount=None):
        image_item = self.get_selected_image()
        if image_item:
            if side is None or crop_amount is None:
                side, ok = QtWidgets.QInputDialog.getItem(
                    self, "Crop Image", "Select side to crop:", ["top", "bottom", "left", "right"], 0, False)
                if not ok or not side:
                    return
                crop_amount, ok = QtWidgets.QInputDialog.getInt(
                    self, "Crop Amount", f"Enter amount to crop from {side} (in pixels):", 10, 1, 1000, 1)
                if not ok:
                    return
            pixmap = image_item.pixmap()
            rect = pixmap.rect()
            if side == 'top':
                rect.setTop(rect.top() + crop_amount)
            elif side == 'bottom':
                rect.setBottom(rect.bottom() - crop_amount)
            elif side == 'left':
                rect.setLeft(rect.left() + crop_amount)
            elif side == 'right':
                rect.setRight(rect.right() - crop_amount)
            else:
                QtWidgets.QMessageBox.warning(self, "Invalid Side",
                                              f"Invalid side '{side}' for cropping. Please choose 'left', 'right', 'top', or 'bottom'.")
                return
            cropped_pixmap = pixmap.copy(rect)
            image_item.setPixmap(cropped_pixmap)
            self.log_command(f"Cropped {crop_amount}px from {side} of Image {self.selected_image_index + 1}")

    def reset_crop_image(self):
        image_item = self.get_selected_image()
        if image_item:
            image_item.setPixmap(image_item.original_pixmap)
            self.center_image()
            self.log_command(f"Reset crop of Image {self.selected_image_index + 1}")

    def move_image(self, dx, dy):
        image_item = self.get_selected_image()
        if image_item:
            image_item.moveBy(dx, dy)
            self.log_command(f"Moved Image {self.selected_image_index + 1} by ({dx}, {dy})")

    def center_image(self):
        self.center_image_horizontally()
        self.center_image_vertically()
        self.log_command(f"Centered Image {self.selected_image_index + 1}")

    def center_image_horizontally(self):
        image_item = self.get_selected_image()
        if image_item:
            scene_width = self.scene.width()
            img_width = image_item.pixmap().width()
            x = (scene_width - img_width) / 2
            image_item.setPos(x, image_item.pos().y())
            self.log_command(f"Centered Image {self.selected_image_index + 1} horizontally")

    def center_image_vertically(self):
        image_item = self.get_selected_image()
        if image_item:
            scene_height = self.scene.height()
            img_height = image_item.pixmap().height()
            y = (scene_height - img_height) / 2
            image_item.setPos(image_item.pos().x(), y)
            self.log_command(f"Centered Image {self.selected_image_index + 1} vertically")

    def snap_to_canvas(self, side=None):
        image_item = self.get_selected_image()
        if image_item:
            if side is None:
                side, ok = QtWidgets.QInputDialog.getItem(self, "Snap to Canvas",
                                                          "Select side to snap to:", ["left", "right", "top", "bottom"], 0, False)
                if not ok or not side:
                    return
            if side == 'right':
                x = self.scene.sceneRect().width() - image_item.pixmap().width()
                y = image_item.pos().y()
            elif side == 'left':
                x = 0
                y = image_item.pos().y()
            elif side == 'top':
                x = image_item.pos().x()
                y = 0
            elif side == 'bottom':
                x = image_item.pos().x()
                y = self.scene.sceneRect().height() - image_item.pixmap().height()
            else:
                QtWidgets.QMessageBox.warning(self, "Invalid Side",
                                              f"Invalid side '{side}' for snapping to canvas. Please choose 'left', 'right', 'top', or 'bottom'.")
                return
            image_item.setPos(x, y)
            self.log_command(f"Snapped Image {self.selected_image_index + 1} to canvas {side}")

    def snap_to_image(self, other_index=None, side=None):
        image_item = self.get_selected_image()
        if image_item:
            if other_index is None or side is None:
                items = [f"Image {i + 1}" for i in range(len(self.images)) if i != self.selected_image_index]
                if not items:
                    QtWidgets.QMessageBox.warning(self, "No Other Images", "There are no other images to snap to.")
                    return
                other_image_str, ok = QtWidgets.QInputDialog.getItem(self, "Snap to Image",
                                                                     "Select image to snap to:", items, 0, False)
                if not ok or not other_image_str:
                    return
                other_index = int(other_image_str.split(' ')[1]) - 1
                side, ok = QtWidgets.QInputDialog.getItem(self, "Snap Side",
                                                          "Select side to snap to:", ["left", "right", "top", "bottom"], 0, False)
                if not ok or not side:
                    return
            other_image = self.images[other_index]
            if side == 'right':
                x = other_image.pos().x() + other_image.pixmap().width()
                y = other_image.pos().y()
            elif side == 'left':
                x = other_image.pos().x() - image_item.pixmap().width()
                y = other_image.pos().y()
            elif side == 'top':
                x = other_image.pos().x()
                y = other_image.pos().y() - image_item.pixmap().height()
            elif side == 'bottom':
                x = other_image.pos().x()
                y = other_image.pos().y() + other_image.pixmap().height()
            else:
                QtWidgets.QMessageBox.warning(self, "Invalid Side",
                                              f"Invalid side '{side}' for snapping to image. Please choose 'left', 'right', 'top', or 'bottom'.")
                return
            image_item.setPos(x, y)
            self.log_command(f"Snapped Image {self.selected_image_index + 1} to {side} of Image {other_index + 1}")

    def log_command(self, command_str):
        self.command_history.append(command_str)
        self.command_list_widget.addItem(command_str)

    def export_commands(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Commands", "", "Text Files (*.txt)")
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    for command in self.command_history:
                        f.write(command + '\n')
                QtWidgets.QMessageBox.information(self, "Export Successful", "Commands exported successfully.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Export Failed", f"An error occurred: {e}")

    def import_commands(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Commands", "", "Text Files (*.txt)")
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    commands = f.read().splitlines()
                # Clear existing commands and images
                self.command_history = []
                self.command_list_widget.clear()
                self.reset_images()
                # Execute commands
                for command in commands:
                    self.command_history.append(command)
                    self.command_list_widget.addItem(command)
                    self.execute_command(command)
                QtWidgets.QMessageBox.information(self, "Import Successful", "Commands imported successfully.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Import Failed", f"An error occurred: {e}")

    def execute_command(self, command_str):
        # Selected Image X
        if command_str.startswith('Selected Image '):
            m = re.match(r'Selected Image (\d+)', command_str)
            if m:
                index = int(m.group(1)) - 1
                self.select_image(index)
            return

        # Rotated Image X by Y degrees
        elif command_str.startswith('Rotated Image '):
            m = re.match(r'Rotated Image (\d+) by (\d+) degrees', command_str)
            if m:
                index = int(m.group(1)) - 1
                angle = int(m.group(2))
                self.select_image(index)
                self.rotate_image(angle=angle)
            return

        # Scaled Image X to fit scene height
        elif 'to fit scene height' in command_str:
            m = re.match(r'Scaled Image (\d+) to fit scene height', command_str)
            if m:
                index = int(m.group(1)) - 1
                self.select_image(index)
                self.scale_image(fit_vertical=True)
            return

        # Scaled Image X to fit scene width
        elif 'to fit scene width' in command_str:
            m = re.match(r'Scaled Image (\d+) to fit scene width', command_str)
            if m:
                index = int(m.group(1)) - 1
                self.select_image(index)
                self.scale_image(fit_vertical=False)
            return

        # Scaled Image X by factor Y
        elif 'Scaled Image ' in command_str and 'by factor' in command_str:
            m = re.match(r'Scaled Image (\d+) by factor ([\d\.]+)', command_str)
            if m:
                index = int(m.group(1)) - 1
                factor = float(m.group(2))
                self.select_image(index)
                self.custom_scale_image(choice='Scale Factor', scale_factor=factor)
            return

        # Set dimensions of Image X to WxH
        elif 'Set dimensions of Image ' in command_str:
            m = re.match(r'Set dimensions of Image (\d+) to (\d+)x(\d+)', command_str)
            if m:
                index = int(m.group(1)) - 1
                width = int(m.group(2))
                height = int(m.group(3))
                self.select_image(index)
                self.custom_scale_image(choice='Set Dimensions', width=width, height=height)
            return

        # Scaled down Image X by 20%
        elif 'Scaled down Image ' in command_str:
            m = re.match(r'Scaled down Image (\d+) by (\d+)%', command_str)
            if m:
                index = int(m.group(1)) - 1
                # Assuming scale down by 20%
                self.select_image(index)
                self.scale_down_image()
            return

        # Cropped Npx from SIDE of Image X
        elif 'Cropped' in command_str and 'from' in command_str and 'of Image' in command_str:
            m = re.match(r'Cropped (\d+)px from (\w+) of Image (\d+)', command_str)
            if m:
                crop_amount = int(m.group(1))
                side = m.group(2)
                index = int(m.group(3)) - 1
                self.select_image(index)
                self.crop_image(side=side, crop_amount=crop_amount)
            return

        # Reset crop of Image X
        elif 'Reset crop of Image ' in command_str:
            m = re.match(r'Reset crop of Image (\d+)', command_str)
            if m:
                index = int(m.group(1)) - 1
                self.select_image(index)
                self.reset_crop_image()
            return

        # Moved Image X by (dx, dy)
        elif 'Moved Image ' in command_str and 'by' in command_str:
            m = re.match(r'Moved Image (\d+) by \((-?\d+), (-?\d+)\)', command_str)
            if m:
                index = int(m.group(1)) - 1
                dx = int(m.group(2))
                dy = int(m.group(3))
                self.select_image(index)
                self.move_image(dx, dy)
            return

        # Centered Image X
        elif 'Centered Image ' in command_str and 'horizontally' not in command_str and 'vertically' not in command_str:
            m = re.match(r'Centered Image (\d+)', command_str)
            if m:
                index = int(m.group(1)) - 1
                self.select_image(index)
                self.center_image()
            return

        # Centered Image X horizontally
        elif 'Centered Image ' in command_str and 'horizontally' in command_str:
            m = re.match(r'Centered Image (\d+) horizontally', command_str)
            if m:
                index = int(m.group(1)) - 1
                self.select_image(index)
                self.center_image_horizontally()
            return

        # Centered Image X vertically
        elif 'Centered Image ' in command_str and 'vertically' in command_str:
            m = re.match(r'Centered Image (\d+) vertically', command_str)
            if m:
                index = int(m.group(1)) - 1
                self.select_image(index)
                self.center_image_vertically()
            return

        # Snapped Image X to canvas SIDE
        elif 'Snapped Image ' in command_str and 'to canvas' in command_str:
            m = re.match(r'Snapped Image (\d+) to canvas (left|right|top|bottom)', command_str)
            if m:
                index = int(m.group(1)) - 1
                side = m.group(2)
                self.select_image(index)
                self.snap_to_canvas(side=side)
            else:
                print(f"Invalid command format: {command_str}")
            return

        # Snapped Image X to SIDE of Image Y
        elif 'Snapped Image ' in command_str and 'to' in command_str and 'of Image' in command_str:
            m = re.match(r'Snapped Image (\d+) to (\w+) of Image (\d+)', command_str)
            if m:
                index = int(m.group(1)) - 1
                side = m.group(2)
                other_index = int(m.group(3)) - 1
                self.select_image(index)
                self.snap_to_image(other_index=other_index, side=side)
            return

        else:
            print(f"Unknown command: {command_str}")

def main():
    image_paths = [
        'selected_boxes/box_642_234.png',
        'selected_boxes/box_943_475.png',
        'selected_boxes/box_979_476.png',
        'selected_boxes/box_1466_227.png'
    ]

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(image_paths)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
