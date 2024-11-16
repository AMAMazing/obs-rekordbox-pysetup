import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class ImageItem(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pixmap, index):
        super().__init__(pixmap)
        self.index = index
        self.setAcceptHoverEvents(True)
        self.default_opacity = 1.0
        self.hover_opacity = 0.6

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
        self.init_ui()

    def init_ui(self):
        # Create the graphics view and scene
        self.graphics_view = QtWidgets.QGraphicsView()
        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        # Set scene size with 16:9 aspect ratio and increase size to avoid scrollbars
        scene_width = 1920  # Increased width
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
        main_layout.addWidget(self.image_selector)
        main_layout.addWidget(self.control_panel)

        container = QtWidgets.QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_images(self):
        for idx, path in enumerate(self.image_paths):
            pixmap = QtGui.QPixmap(path)
            # Scale images initially
            scale_ratio = 0.3
            pixmap = pixmap.scaled(int(pixmap.width() * scale_ratio),
                                   int(pixmap.height() * scale_ratio),
                                   QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            image_item = ImageItem(pixmap, idx)
            image_item.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable)
            image_item.setPos(idx * 300, 100)
            self.scene.addItem(image_item)
            self.images.append(image_item)

        # Set the first image as selected by default
        if self.images:
            self.selected_image_index = 0
            self.images[0].setSelected(True)

    def create_control_panel(self):
        # Image Selector Buttons
        self.image_selector = QtWidgets.QWidget()
        selector_layout = QtWidgets.QHBoxLayout()
        selector_label = QtWidgets.QLabel("Select Image:")
        selector_layout.addWidget(selector_label)

        for idx in range(len(self.images)):
            btn = QtWidgets.QPushButton(f"Image {idx + 1}")
            btn.clicked.connect(lambda _, i=idx: self.select_image(i))
            selector_layout.addWidget(btn)

        self.image_selector.setLayout(selector_layout)

        # Control Panel for selected image
        self.control_panel = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()

        # Rotate button
        rotate_btn = QtWidgets.QPushButton("Rotate Image")
        rotate_btn.clicked.connect(self.rotate_image)
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
        custom_scale_btn.clicked.connect(self.custom_scale_image)
        layout.addWidget(custom_scale_btn, 0, 3)

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

        # Snap to image button
        snap_to_image_btn = QtWidgets.QPushButton("Snap to Image")
        snap_to_image_btn.clicked.connect(self.snap_to_image)
        layout.addWidget(snap_to_image_btn, 2, 2)

        self.control_panel.setLayout(layout)

    def select_image(self, index):
        # Deselect previous image
        if self.selected_image_index is not None:
            self.images[self.selected_image_index].setSelected(False)
        # Select new image
        self.selected_image_index = index
        self.images[index].setSelected(True)

    def get_selected_image(self):
        if self.selected_image_index is not None:
            return self.images[self.selected_image_index]
        else:
            QtWidgets.QMessageBox.warning(self, "No Image Selected", "Please select an image to manipulate.")
            return None

    def rotate_image(self):
        image_item = self.get_selected_image()
        if image_item:
            pixmap = image_item.pixmap().transformed(QtGui.QTransform().rotate(90), QtCore.Qt.SmoothTransformation)
            image_item.setPixmap(pixmap)
            # Center image after rotation
            self.center_image()

    def scale_image(self, fit_vertical=False):
        image_item = self.get_selected_image()
        if image_item:
            scene_rect = self.scene.sceneRect()
            if fit_vertical:
                # Scale to fit the full scene height
                new_height = int(scene_rect.height())
                pixmap = image_item.pixmap().scaledToHeight(new_height, QtCore.Qt.SmoothTransformation)
            else:
                # Scale to fit the full scene width
                new_width = int(scene_rect.width())
                pixmap = image_item.pixmap().scaledToWidth(new_width, QtCore.Qt.SmoothTransformation)
            image_item.setPixmap(pixmap)
            # Center image after scaling
            self.center_image()

    def custom_scale_image(self):
        image_item = self.get_selected_image()
        if image_item:
            choice, ok = QtWidgets.QInputDialog.getItem(
                self, "Custom Scaling", "Choose scaling method:", ["Scale Factor", "Set Dimensions"], 0, False)
            if ok and choice:
                if choice == "Scale Factor":
                    scale_factor, ok = QtWidgets.QInputDialog.getDouble(
                        self, "Scale Factor", "Enter scale factor:", 1.0, 0.1, 10.0, 2)
                    if ok:
                        pixmap = image_item.pixmap()
                        new_width = int(pixmap.width() * scale_factor)
                        new_height = int(pixmap.height() * scale_factor)
                        pixmap = pixmap.scaled(new_width, new_height, QtCore.Qt.KeepAspectRatio,
                                               QtCore.Qt.SmoothTransformation)
                        image_item.setPixmap(pixmap)
                        # Center image after scaling
                        self.center_image()
                elif choice == "Set Dimensions":
                    width, ok_w = QtWidgets.QInputDialog.getInt(
                        self, "Set Width", "Enter new width:", value=image_item.pixmap().width(), min=1)
                    height, ok_h = QtWidgets.QInputDialog.getInt(
                        self, "Set Height", "Enter new height:", value=image_item.pixmap().height(), min=1)
                    if ok_w and ok_h:
                        pixmap = image_item.pixmap().scaled(width, height, QtCore.Qt.IgnoreAspectRatio,
                                                            QtCore.Qt.SmoothTransformation)
                        image_item.setPixmap(pixmap)
                        # Center image after scaling
                        self.center_image()

    def move_image(self, dx, dy):
        image_item = self.get_selected_image()
        if image_item:
            image_item.moveBy(dx, dy)

    def center_image(self):
        self.center_image_horizontally()
        self.center_image_vertically()

    def center_image_horizontally(self):
        image_item = self.get_selected_image()
        if image_item:
            scene_width = self.scene.width()
            img_width = image_item.pixmap().width()
            x = (scene_width - img_width) / 2
            image_item.setPos(x, image_item.pos().y())

    def center_image_vertically(self):
        image_item = self.get_selected_image()
        if image_item:
            scene_height = self.scene.height()
            img_height = image_item.pixmap().height()
            y = (scene_height - img_height) / 2
            image_item.setPos(image_item.pos().x(), y)

    def snap_to_image(self):
        image_item = self.get_selected_image()
        if image_item:
            items = [f"Image {i + 1}" for i in range(len(self.images)) if i != self.selected_image_index]
            if not items:
                QtWidgets.QMessageBox.warning(self, "No Other Images", "There are no other images to snap to.")
                return
            other_image_str, ok = QtWidgets.QInputDialog.getItem(self, "Snap to Image",
                                                                 "Select image to snap to:", items, 0, False)
            if ok and other_image_str:
                other_index = int(other_image_str.split(' ')[1]) - 1
                side, ok = QtWidgets.QInputDialog.getItem(self, "Snap Side",
                                                          "Select side to snap to:", ["left", "right", "top", "bottom"], 0, False)
                if ok and side:
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
                    image_item.setPos(x, y)

def main():
    image_paths = [
        'selected_boxes/box_642_234.png',
        'selected_boxes/box_943_475.png',
        'selected_boxes/box_979_476.png',
        'selected_boxes/box_1466_227.png'
    ]

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(image_paths)
    window.showMaximized()  # Maximize the window to fit the larger scene
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
