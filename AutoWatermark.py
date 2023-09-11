import cv2, os, sys
import numpy as np
from glob import glob
import PyQt5
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PIL import Image


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


main_ui = resource_path("AutoWatermark.ui")
Ui_MainWindow = uic.loadUiType(main_ui)[0]


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

        self.button0 = QPushButton("Select JPG images folder", self)
        self.button0.clicked.connect(self.button0Clicked)
        buttonLayout.addWidget(self.button0)

        self.button1 = QPushButton("Select white watermark PNG", self)
        self.button1.clicked.connect(self.button1Clicked)
        buttonLayout.addWidget(self.button1)

        self.button2 = QPushButton("Select black watermark PNG", self)
        self.button2.clicked.connect(self.button2Clicked)
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

    def get_position(self):
        for row in range(3):
            for col in range(3):
                if self.radioButtons[row][col].isChecked():
                    return row, col
        self.text.append("Got an error on selecting watermark position!")
        return None

    def button0Clicked(self):
        fname = QFileDialog.getExistingDirectory(self, "Select Folder", "")
        self.images = glob(f"{fname}/*.jpg")
        self.images = glob(f"{fname}/*.jpeg") + self.images
        self.images = glob(f"{fname}/*.JPG") + self.images
        self.images = glob(f"{fname}/*.JPEG") + self.images
        print(self.images)
        self.text.append(f"JPG folder selected: {fname}")

    def button1Clicked(self):
        fname = QFileDialog.getOpenFileName(
            self, "Select White Watermark", "", "PNG Files (*.png)"
        )
        self.white = fname[0]
        self.text.append(f"White watermark selected: {fname[0]}")

    def button2Clicked(self):
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
                new_file_path = os.path.join(
                    new_dir, filename[:-4] + "_watermarked.jpg"
                )
                with open(new_file_path, "wb") as f:
                    result_image.save(f, **info)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())

# >> pyinstaller -w -F --add-data="AutoWatermark.ui;./" AutoWatermark.py
