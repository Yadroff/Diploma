import image_viewer

import pyqt_bounding_box
import pyqtree
import csv

from PyQt5.Qt import *


class BBoxEditor:
    def __init__(self, filename, shape: QSize):
        self.bboxes = pyqtree.Index(bbox=(0, 0, shape.width(), shape.height()))
        with open(filename, 'r', newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=' ')
            for row in reader:
                x_min, y_min, x_max, y_max = map(float, row[1:])
                bbox = pyqt_bounding_box.BoundingBox()
                bbox.setSize(x_max - x_min, y_max - y_min)
                bbox.setPos(x_min, y_max)
                bbox.setColor(Qt.red)
                bbox.setStyle(Qt.SolidLine)
                bbox.show()
                self.bboxes.insert(bbox, (x_min, y_min, x_max, y_max))
