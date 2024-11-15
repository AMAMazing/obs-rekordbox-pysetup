import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class ImageItem:
    def __init__(self, pixmap, index, scene):
        self.pixmap = pixmap
        self.index = index
        self.scene = scene
        self.pixmap_item = self.scene.addPixmap(self.pixmap)
        self.position = QtCore.QPointF(0, 0)
        self.pixmap_item.setPos(self.position)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.pixmap_item.setPixmap(self.pixmap)

    def set_position(self, x, y):
        self.position = QtCore.QPointF(x, y)
        self.pixmap_item.setPos(self.position)

    def move_by(self, dx, dy):
        self.position += QtCore.QPointF(dx, dy)
        self.pixmap_item.setPos(self.position)

    def center_horizontally(self):
        scene_width = self.scene.width()
        x = (scene_width - self.pixmap.width()) / 2
        self.set_position(x, self.position.y())

    def center_vertically(self):
        scene_height = self.scene.height()
        y = (scene_height - self.pixmap.height()) / 2
        self.set_position(self.position.x(), y)

    def snap_to_image(self, other_image, side='right'):
        if side == 'right':
            x = other_image.position.x() + other_image.pixmap.width()
            y = other_image.position.y()
        elif side == 'left':
            x = other_image.position.x() - self.pixmap.width()
            y = other_image.position.y()
        elif side == 'top':
            x = other_image.position.x()
            y = other_image.position.y() - self.pixmap.height()
        elif side == 'bottom':
            x = other_image.position.x()
            y = other_image.position.y() + other_image.pixmap.height()
        self.set_position(x, y)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, image_paths):
        super().__init__()
        self.setWindowTitle("Advanced Image Manipulation GUI")
        self.image_paths = image_paths
        self.images = []
        self.init_ui()

    def init_ui(self):
        # Create the graphics view and scene
        self.graphics_view = QtWidgets.QGraphicsView()
        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        # Set scene size with 16:9 aspect ratio
        scene_width = 1280
        scene_height = int(scene_width * 9 / 16)
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
        self.graphics_view.setFixedSize(scene_width, scene_height)

        # Load images
        self.load_images()

        # Create control panel
        self.create_control_panel()

        # Set layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.graphics_view)
        main_layout.addWidget(self.control_panel)

        container = QtWidgets.QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_images(self):
        for idx, path in enumerate(self.image_paths):
            pixmap = QtGui.QPixmap(path)
            # Scale images initially
            scale_ratio = 0.3
            pixmap = pixmap.scaled(int(pixmap.width() * scale_ratio), int(pixmap.height() * scale_ratio),
                                   QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            image_item = ImageItem(pixmap, idx, self.scene)
            # Position images at different spots
            image_item.set_position(idx * 200, 100)
            self.images.append(image_item)

    def create_control_panel(self):
        self.control_panel = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()

        for idx in range(len(self.images)):
            frame = QtWidgets.QFrame()
            frame_layout = QtWidgets.QVBoxLayout()

            # Rotate button
            rotate_btn = QtWidgets.QPushButton(f"Rotate Image {idx+1}")
            rotate_btn.clicked.connect(lambda _, i=idx: self.rotate_image(i))
            frame_layout.addWidget(rotate_btn)

            # Scale buttons
            scale_vert_btn = QtWidgets.QPushButton(f"Scale Vertically Image {idx+1}")
            scale_vert_btn.clicked.connect(lambda _, i=idx: self.scale_image(i, fit_vertical=True))
            frame_layout.addWidget(scale_vert_btn)

            scale_horiz_btn = QtWidgets.QPushButton(f"Scale Horizontally Image {idx+1}")
            scale_horiz_btn.clicked.connect(lambda _, i=idx: self.scale_image(i, fit_vertical=False))
            frame_layout.addWidget(scale_horiz_btn)

            # Custom scale button
            custom_scale_btn = QtWidgets.QPushButton(f"Custom Scale Image {idx+1}")
            custom_scale_btn.clicked.connect(lambda _, i=idx: self.custom_scale_image(i))
            frame_layout.addWidget(custom_scale_btn)

            # Movement buttons
            move_left_btn = QtWidgets.QPushButton(f"Move Left Image {idx+1}")
            move_left_btn.clicked.connect(lambda _, i=idx: self.move_image(i, -20, 0))
            frame_layout.addWidget(move_left_btn)

            move_right_btn = QtWidgets.QPushButton(f"Move Right Image {idx+1}")
            move_right_btn.clicked.connect(lambda _, i=idx: self.move_image(i, 20, 0))
            frame_layout.addWidget(move_right_btn)

            move_up_btn = QtWidgets.QPushButton(f"Move Up Image {idx+1}")
            move_up_btn.clicked.connect(lambda _, i=idx: self.move_image(i, 0, -20))
            frame_layout.addWidget(move_up_btn)

            move_down_btn = QtWidgets.QPushButton(f"Move Down Image {idx+1}")
            move_down_btn.clicked.connect(lambda _, i=idx: self.move_image(i, 0, 20))
            frame_layout.addWidget(move_down_btn)

            # Centering buttons
            center_horiz_btn = QtWidgets.QPushButton(f"Center Horizontally Image {idx+1}")
            center_horiz_btn.clicked.connect(lambda _, i=idx: self.center_image_horizontally(i))
            frame_layout.addWidget(center_horiz_btn)

            center_vert_btn = QtWidgets.QPushButton(f"Center Vertically Image {idx+1}")
            center_vert_btn.clicked.connect(lambda _, i=idx: self.center_image_vertically(i))
            frame_layout.addWidget(center_vert_btn)

            # Snap to image buttons
            snap_to_image_btn = QtWidgets.QPushButton(f"Snap to Image {idx+1}")
            snap_to_image_btn.clicked.connect(lambda _, i=idx: self.snap_to_image(i))
            frame_layout.addWidget(snap_to_image_btn)

            frame.setLayout(frame_layout)
            layout.addWidget(frame)

        self.control_panel.setLayout(layout)

    def rotate_image(self, index):
        pixmap = self.images[index].pixmap.transformed(QtGui.QTransform().rotate(90), QtCore.Qt.SmoothTransformation)
        self.images[index].set_pixmap(pixmap)
        # Center image after rotation
        self.center_image(index)

    def scale_image(self, index, fit_vertical=False):
        scene_rect = self.scene.sceneRect()
        if fit_vertical:
            # Scale to fit the full scene height
            new_height = int(scene_rect.height())
            pixmap = self.images[index].pixmap.scaledToHeight(new_height, QtCore.Qt.SmoothTransformation)
        else:
            # Scale to fit the full scene width
            new_width = int(scene_rect.width())
            pixmap = self.images[index].pixmap.scaledToWidth(new_width, QtCore.Qt.SmoothTransformation)
        self.images[index].set_pixmap(pixmap)
        # Center image after scaling
        self.center_image(index)

    def custom_scale_image(self, index):
        choice, ok = QtWidgets.QInputDialog.getItem(
            self, "Custom Scaling", "Choose scaling method:", ["Scale Factor", "Set Dimensions"], 0, False)
        if ok and choice:
            if choice == "Scale Factor":
                scale_factor, ok = QtWidgets.QInputDialog.getDouble(
                    self, "Scale Factor", f"Enter scale factor for Image {index + 1}:", 1.0, 0.1, 10.0, 2)
                if ok:
                    pixmap = self.images[index].pixmap
                    new_width = int(pixmap.width() * scale_factor)
                    new_height = int(pixmap.height() * scale_factor)
                    pixmap = pixmap.scaled(new_width, new_height, QtCore.Qt.KeepAspectRatio,
                                           QtCore.Qt.SmoothTransformation)
                    self.images[index].set_pixmap(pixmap)
                    # Center image after scaling
                    self.center_image(index)
            elif choice == "Set Dimensions":
                width, ok_w = QtWidgets.QInputDialog.getInt(
                    self, "Set Width", f"Enter new width for Image {index + 1}:", value=self.images[index].pixmap.width(), min=1)
                height, ok_h = QtWidgets.QInputDialog.getInt(
                    self, "Set Height", f"Enter new height for Image {index + 1}:", value=self.images[index].pixmap.height(), min=1)
                if ok_w and ok_h:
                    pixmap = self.images[index].pixmap.scaled(width, height, QtCore.Qt.IgnoreAspectRatio,
                                                              QtCore.Qt.SmoothTransformation)
                    self.images[index].set_pixmap(pixmap)
                    # Center image after scaling
                    self.center_image(index)

    def move_image(self, index, dx, dy):
        self.images[index].move_by(dx, dy)

    def center_image(self, index):
        self.center_image_horizontally(index)
        self.center_image_vertically(index)

    def center_image_horizontally(self, index):
        self.images[index].center_horizontally()

    def center_image_vertically(self, index):
        self.images[index].center_vertically()

    def snap_to_image(self, index):
        # Ask user for the other image index and side
        items = [f"Image {i+1}" for i in range(len(self.images)) if i != index]
        if not items:
            QtWidgets.QMessageBox.warning(self, "No Other Images", "There are no other images to snap to.")
            return
        other_image_str, ok = QtWidgets.QInputDialog.getItem(self, "Snap to Image",
                                                             f"Select image to snap Image {index + 1} to:", items, 0, False)
        if ok and other_image_str:
            other_index = int(other_image_str.split(' ')[1]) - 1
            side, ok = QtWidgets.QInputDialog.getItem(self, "Snap Side",
                                                      "Select side to snap to:", ["left", "right", "top", "bottom"], 0, False)
            if ok and side:
                self.images[index].snap_to_image(self.images[other_index], side)

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
