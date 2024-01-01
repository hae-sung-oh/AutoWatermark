"""
=============================== AutoWatermark Application ===============================

This application allows users to apply watermarks to a batch of images.
Users can select images, choose a white and a black watermark, and apply
these watermarks to the images based on the image's brightness automatically.

How to Use:
1. Drag and drop images or click and select an image folder using the 'Input images' button.
2. Drag and drop or click and select a white watermark PNG file using the 'White watermark' button.
3. Drag and drop or click and select a black watermark PNG file using the 'Black watermark' button.
4. Choose the watermark position and size.
5. Click 'Apply!' to process the images.
6. Processed images will be saved in a 'Modified' folder or overwrited on the original images.
=========================================================================================
"""

import cv2, os, sys
import numpy as np
from glob import glob
import PyQt5
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PIL import Image


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


main_ui = resource_path("AutoWatermark.ui")
Ui_MainWindow = uic.loadUiType(main_ui)[0]


class Button(QPushButton):
    def __init__(
        self, title, fileTypes, drop_callback, clicked_callback, batch=True, parent=None
    ):
        super().__init__(title, parent)
        self.fileTypes = fileTypes
        self.callback = drop_callback
        # self.setAlignment(Qt.AlignCenter)
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setText(title)
        self.setAcceptDrops(True)
        self.clicked.connect(clicked_callback)
        self.batch = batch

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # and all(
            #     url.toLocalFile().endswith(self.fileTypes)
            #     for url in event.mimeData().urls()
            # ):
            event.accept()
            self.setStyleSheet("background-color: lightgreen;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event):
        self.setStyleSheet("")
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.callback(files)


class MainWindow(QWidget, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.show()

    def initUI(self):
        self.images = []
        self.white = None
        self.black = None

        self.resize(900, 300)

        mainLayout = QVBoxLayout()

        topLayout = QHBoxLayout()
        self.text = QTextBrowser(self)
        self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        topLayout.addWidget(self.text)

        self.groupBox = QGroupBox("Watermark Position")
        self.groupBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        gridLayout = QGridLayout()

        self.radioButtons = []
        for row in range(3):
            rowButtons = []
            for col in range(3):
                radioButton = QRadioButton()
                gridLayout.addWidget(radioButton, row, col)
                rowButtons.append(radioButton)
                if row == 2 and col == 2:
                    radioButton.setChecked(True)
            self.radioButtons.append(rowButtons)

        self.groupBox.setLayout(gridLayout)
        topLayout.addWidget(self.groupBox)

        topWidget = QWidget()
        topWidget.setLayout(topLayout)
        mainLayout.addWidget(topWidget)

        buttonLayout = QHBoxLayout()

        self.button0 = Button(
            "Input images",
            [".jpg", ".jpeg", ".JPG", "JPEG"],
            self.addImages,
            self.button0Clicked,
            True,
            self,
        )
        buttonLayout.addWidget(self.button0)

        self.button1 = Button(
            "White watermark",
            [".png", ".PNG"],
            self.addWhiteWatermark,
            self.button1Clicked,
            False,
            self,
        )
        buttonLayout.addWidget(self.button1)

        self.button2 = Button(
            "Black watermark",
            [".png", ".PNG"],
            self.addBlackWatermark,
            self.button2Clicked,
            False,
            self,
        )
        buttonLayout.addWidget(self.button2)

        self.watermarkSizeInput = QDoubleSpinBox(self)
        self.watermarkSizeInput.setRange(0, 1)
        self.watermarkSizeInput.setSingleStep(0.01)
        self.watermarkSizeInput.setValue(0.18)
        self.watermarkSizeInput.setToolTip("Watermark size ratio (0 to 1)")
        buttonLayout.addWidget(self.watermarkSizeInput)

        self.overwriteCheckbox = QCheckBox("Overwrite", self)
        buttonLayout.addWidget(self.overwriteCheckbox)

        self.button3 = QPushButton("Apply!", self)
        self.button3.clicked.connect(self.button3Clicked)
        buttonLayout.addWidget(self.button3)

        buttonWidget = QWidget()
        buttonWidget.setLayout(buttonLayout)
        mainLayout.addWidget(buttonWidget)

        self.setLayout(mainLayout)

        self.setAcceptDrops(True)

        self.text.append(__doc__)

    def addImages(self, files):
        self.images = []
        if os.path.isdir(files[0]):
            self.addImagesFromDirectory(files[0])
        else:
            for file in files:
                if os.path.isfile(file) and file.lower().endswith(
                    (".jpg", ".jpeg", ".png")
                ):
                    self.images.append(file)
            self.updateImageListDisplay()

    def addWhiteWatermark(self, files):
        self.white = None
        if files and files[0].endswith((".png", ".PNG")):
            self.white = files[0]
            self.text.append(f"White watermark selected: {self.white}")
        else:
            self.text.append(
                "White watermark import failed. Only PNG format is allowed."
            )

    def addBlackWatermark(self, files):
        self.black = None
        if files and files[0].endswith((".png", ".PNG")):
            self.black = files[0]
            self.text.append(f"Black watermark selected: {self.black}")
        else:
            self.text.append(
                "Black watermark import failed. Only PNG format is allowed."
            )

    def addImagesFromDirectory(self, directory):
        for ext in ("*/.jpg", "/*.jpeg", "/*.JPG", "/*.JPEG"):
            self.images.extend(glob(os.path.join(directory, ext)))
        self.text.append(f"JPG folder selected: {directory}")

    def updateImageListDisplay(self):
        # self.text.clear()
        self.text.append("Images to process:")
        for img in self.images:
            self.text.append(img)

    def get_position(self):
        for row in range(3):
            for col in range(3):
                if self.radioButtons[row][col].isChecked():
                    return row, col
        self.text.append("Got an error on selecting watermark position!")
        return None

    def button0Clicked(self):
        self.images = []
        fname = QFileDialog.getExistingDirectory(self, "Select Folder", "")
        self.addImagesFromDirectory(fname)

    def button1Clicked(self):
        self.white = None
        fname = QFileDialog.getOpenFileName(
            self, "Select White Watermark", "", "PNG Files (*.png)"
        )
        self.white = fname[0]
        self.text.append(f"White watermark selected: {fname[0]}")

    def button2Clicked(self):
        self.black = None
        fname = QFileDialog.getOpenFileName(
            self, "Select Black Watermark", "", "PNG Files (*.png)"
        )
        self.black = fname[0]
        self.text.append(f"Black watermark selected: {fname[0]}")

    def button3Clicked(self):
        self.AutoWatermark(
            self.images, self.watermarkSizeInput.value(), self.white, self.black
        )
        self.text.append("Applying watermarks complete!")

    def kor_imread(self, path):
        img_array = np.fromfile(path, np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    def kor_pngread(self, path):
        img_array = np.fromfile(path, np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)

    def AutoWatermark(self, image, ratio, white, black):
        position = self.get_position()
        if position is None:
            return

        row, col = position

        white_logo = self.kor_pngread(white)
        black_logo = self.kor_pngread(black)
        try:
            assert white_logo.shape[:2] == black_logo.shape[:2]
        except AssertionError:
            self.text.append(
                "Size of white and black watermark is different! Please try again."
            )
            return

        for item in image:
            item = item.replace("\\", "/").replace("\\\\", "/")
            with open(item, "rb") as f:
                meta = Image.open(f)
            info = meta.info

            img = self.kor_imread(item)
            if img is None:
                self.text.append(f"Failed to read image: {item}")
                continue

            h_img, w_img, _ = img.shape
            h_logo, w_logo, _ = white_logo.shape

            dst = img[
                int(h_img - h_logo) : h_img,
                int(w_img - w_logo) : w_img,
            ]

            if np.mean(dst) / 255 < 0.4:
                logo = white_logo
            else:
                logo = black_logo

            min_dim = min(h_img, w_img)
            logo = cv2.resize(
                logo,
                (int(min_dim * ratio), int(min_dim * ratio * h_logo / w_logo)),
                interpolation=cv2.INTER_CUBIC,
            )
            h_logo, w_logo, _ = logo.shape

            alpha = logo[:, :, 3]
            rgb = logo[:, :, :3]

            alpha = np.expand_dims(alpha, axis=2)
            alpha = np.repeat(alpha, 3, axis=2)

            center_y = (
                h_img - h_logo / 2
                if row == 2
                else (h_logo / 2 if row == 0 else h_img / 2)
            )
            center_x = (
                w_img - w_logo / 2
                if col == 2
                else (w_logo / 2 if col == 0 else w_img / 2)
            )

            top_y = int(center_y - h_logo / 2)
            bottom_y = top_y + h_logo
            left_x = int(center_x - w_logo / 2)
            right_x = left_x + w_logo

            destination = img[top_y:bottom_y, left_x:right_x]
            result = cv2.multiply(destination.astype(float), (1 - (alpha / 255)))
            result += cv2.multiply(rgb.astype(float), (alpha / 255))
            result = result.astype(np.uint8)

            img[top_y:bottom_y, left_x:right_x] = result

            result_image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            if self.overwriteCheckbox.isChecked():
                # Overwrite the original image
                with open(item, "wb") as f:
                    result_image.save(f, **info)
            else:
                # Save as a new file
                new_dir = os.path.dirname(item) + "/Modified"
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir)

                filename = os.path.basename(item)
                new_file_path = os.path.join(new_dir, filename)
                with open(new_file_path, "wb") as f:
                    result_image.save(f, **info)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())

# >> pyinstaller -w -F --add-data="AutoWatermark.ui;./" AutoWatermark.py
