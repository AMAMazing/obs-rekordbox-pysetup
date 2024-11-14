import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class ImageItem(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pixmap, index):
        super().__init__(pixmap)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable |
                      QtWidgets.QGraphicsItem.ItemIsSelectable |
                      QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges)
        self.index = index  # Keep track of image index for identification

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            # Snap to grid or other images if close enough
            if self.scene() is not None:
                new_pos = value  # value is already a QPointF
                snapped_pos = self.snap_to_grid(new_pos)
                return snapped_pos  # Return the adjusted QPointF
            else:
                # If not in a scene, can't snap, return original position
                return value
        return super().itemChange(change, value)

    def snap_to_grid(self, pos):
        scene = self.scene()
        if scene is None:
            return pos  # Can't snap without a scene, return original position

        snap_threshold = 20  # Pixels for snapping
        x, y = pos.x(), pos.y()
        img_width = self.pixmap().width()
        img_height = self.pixmap().height()

        # Snap to scene edges
        scene_rect = scene.sceneRect()
        if abs(x) < snap_threshold:
            x = 0
        elif abs(x + img_width - scene_rect.width()) < snap_threshold:
            x = scene_rect.width() - img_width

        if abs(y) < snap_threshold:
            y = 0
        elif abs(y + img_height - scene_rect.height()) < snap_threshold:
            y = scene_rect.height() - img_height

        # Snap to other images
        for item in scene.items():
            if item is not self and isinstance(item, ImageItem):
                other_rect = item.sceneBoundingRect()
                my_rect = self.sceneBoundingRect()

                # Horizontal snapping
                if abs(my_rect.left() - other_rect.right()) < snap_threshold:
                    x = other_rect.right()
                elif abs(my_rect.right() - other_rect.left()) < snap_threshold:
                    x = other_rect.left() - img_width

                # Vertical snapping
                if abs(my_rect.top() - other_rect.bottom()) < snap_threshold:
                    y = other_rect.bottom()
                elif abs(my_rect.bottom() - other_rect.top()) < snap_threshold:
                    y = other_rect.top() - img_height

        return QtCore.QPointF(x, y)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, image_paths):
        super().__init__()
        self.setWindowTitle("Advanced Image Manipulation GUI")
        self.image_paths = image_paths
        self.images = []
        self.image_items = []
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
            self.images.append(pixmap)

            image_item = ImageItem(pixmap, idx)
            # Position images at different spots
            image_item.setPos(idx * 200, 100)
            self.scene.addItem(image_item)
            self.image_items.append(image_item)

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

            # Scale Vertically button
            scale_vert_btn = QtWidgets.QPushButton(f"Scale Vertically Image {idx+1}")
            scale_vert_btn.clicked.connect(lambda _, i=idx: self.scale_image(i, fit_vertical=True))
            frame_layout.addWidget(scale_vert_btn)

            # Scale Horizontally button
            scale_horiz_btn = QtWidgets.QPushButton(f"Scale Horizontally Image {idx+1}")
            scale_horiz_btn.clicked.connect(lambda _, i=idx: self.scale_image(i, fit_vertical=False))
            frame_layout.addWidget(scale_horiz_btn)

            # Custom Scale button
            custom_scale_btn = QtWidgets.QPushButton(f"Custom Scale Image {idx+1}")
            custom_scale_btn.clicked.connect(lambda _, i=idx: self.custom_scale_image(i))
            frame_layout.addWidget(custom_scale_btn)

            frame.setLayout(frame_layout)
            layout.addWidget(frame)

        self.control_panel.setLayout(layout)

    def rotate_image(self, index):
        pixmap = self.images[index].transformed(QtGui.QTransform().rotate(90), QtCore.Qt.SmoothTransformation)
        self.images[index] = pixmap
        self.image_items[index].setPixmap(pixmap)
        self.center_image(index)

    def scale_image(self, index, fit_vertical=False):
        scene_rect = self.scene.sceneRect()
        if fit_vertical:
            # Scale to fit the full scene height
            new_height = int(scene_rect.height())
            pixmap = self.images[index].scaledToHeight(new_height, QtCore.Qt.SmoothTransformation)
        else:
            # Scale to fit the full scene width
            new_width = int(scene_rect.width())
            pixmap = self.images[index].scaledToWidth(new_width, QtCore.Qt.SmoothTransformation)
        self.images[index] = pixmap
        self.image_items[index].setPixmap(pixmap)
        self.center_image(index)

    def custom_scale_image(self, index):
        choice, ok = QtWidgets.QInputDialog.getItem(
            self, "Custom Scaling", "Choose scaling method:", ["Scale Factor", "Set Dimensions"], 0, False)
        if ok and choice:
            if choice == "Scale Factor":
                scale_factor, ok = QtWidgets.QInputDialog.getDouble(
                    self, "Scale Factor", f"Enter scale factor for Image {index + 1}:", 1.0, 0.1, 10.0, 2)
                if ok:
                    pixmap = self.images[index]
                    new_width = int(pixmap.width() * scale_factor)
                    new_height = int(pixmap.height() * scale_factor)
                    pixmap = pixmap.scaled(new_width, new_height, QtCore.Qt.KeepAspectRatio,
                                           QtCore.Qt.SmoothTransformation)
                    self.images[index] = pixmap
                    self.image_items[index].setPixmap(pixmap)
                    self.center_image(index)
            elif choice == "Set Dimensions":
                width, ok_w = QtWidgets.QInputDialog.getInt(
                    self, "Set Width", f"Enter new width for Image {index + 1}:", value=self.images[index].width(), min=1)
                height, ok_h = QtWidgets.QInputDialog.getInt(
                    self, "Set Height", f"Enter new height for Image {index + 1}:", value=self.images[index].height(), min=1)
                if ok_w and ok_h:
                    pixmap = self.images[index].scaled(width, height, QtCore.Qt.IgnoreAspectRatio,
                                                       QtCore.Qt.SmoothTransformation)
                    self.images[index] = pixmap
                    self.image_items[index].setPixmap(pixmap)
                    self.center_image(index)

    def center_image(self, index):
        pixmap = self.images[index]
        img_width = pixmap.width()
        img_height = pixmap.height()
        scene_rect = self.scene.sceneRect()
        x = max((scene_rect.width() - img_width) / 2, 0)
        y = max((scene_rect.height() - img_height) / 2, 0)
        self.image_items[index].setPos(x, y)

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
