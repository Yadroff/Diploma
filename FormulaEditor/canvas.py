# MIT License
#
# Copyright (c) 2021 Paul
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import tkinter as tk
from tkinter import TclError
from tkinter.font import Font
import rtree

import math


def distance_from_point_to_rectangle(point, rect_coords):
    """
    Вычисляет расстояние от точки до прямоугольника, заданного координатами (x_min, y_min, x_max, y_max).

    :param point: Точка в виде кортежа (x, y).
    :param rect_coords: Координаты прямоугольника в виде кортежа (x_min, y_min, x_max, y_max).
    :return: Расстояние от точки до прямоугольника.
    """
    # Переводим координаты точки и прямоугольника в числа
    point_x, point_y = point
    rect_x_min, rect_y_min, rect_x_max, rect_y_max = rect_coords

    # Вычисляем углы прямоугольника
    top_left = (rect_x_min, rect_y_min)
    top_right = (rect_x_max, rect_y_min)
    bottom_right = (rect_x_max, rect_y_max)
    bottom_left = (rect_x_min, rect_y_max)

    # Находим ближайший угол к точке
    closest_corner = min([
        (top_left, math.hypot(point_x - rect_x_min, point_y - rect_y_min)),
        (top_right, math.hypot(point_x - rect_x_max, point_y - rect_y_min)),
        (bottom_right, math.hypot(point_x - rect_x_max, point_y - rect_y_max)),
        (bottom_left, math.hypot(point_x - rect_x_min, point_y - rect_y_max))
    ], key=lambda tup: tup[1])[0]

    # Вычисляем расстояние от точки до ближайшего угла
    dx = point_x - closest_corner[0]
    dy = point_y - closest_corner[1]
    return math.hypot(dx, dy)


class Canvas(tk.Canvas):
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4

    cursors = {TOP_LEFT: 'size_nw_se', TOP_RIGHT: 'size_ne_sw',
               BOTTOM_LEFT: 'size_ne_sw',
               BOTTOM_RIGHT: 'size_nw_se'}  # WINDOWS SPECIFIC CURSORS IN MAC IT MIGHT BE resizetopright, resizetopright etc

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        self.bind('<1>', self.checkCanvasItem)
        self.bind('<ButtonRelease-1>', self.release)
        self._current_item = None
        self._previous_item = None
        self._current_resize_rect = None
        self._tag = 'resize'
        self.resizePoints = {}  # stores the resize points
        self._current_point = None
        self.previous = (0, 0)  # previous mouse coordinates
        self._bboxes = rtree.Index()

    def create_rectangle(self, *args, **kw):
        id = super().create_rectangle(*args, **kw)
        coords = args[0]
        self._bboxes.insert(id, coords)
        return id

    def release(self, event):

        self.unbind('<B1-Motion>')
        self._current_point = None

    def findInBBox(self, items,
                   event):  # when an items overlaps find_closest does't work well so check which item is best fit
        for x in items[1:]:
            if x != self._current_item and self.check_in_bbox(x, event.x, event.y):
                return x

    def find_without_image(self, items):
        if 1 in items:
            if len(items) != 1:
                self._current_item = items[1]
            else:
                self._current_item = None
        else:
            self._current_item = items[0]

    def checkCanvasItem(self, event):

        self._previous_item = self._current_item

        x, y = self.canvasx(event.x), self.canvasy(event.y)
        print(f'CLICK EVENT: {x, y}')
        id = list(self._bboxes.nearest((x, y), 1))[0]
        print(id)
        coords = self.coords(id)
        print(f'CLICK EVENT: Nearest coords: {coords}')
        if len(coords) == 0:
            self._current_item = None
        else:
            if self.check_in_bbox(id, x, y):
                print(f'In bbox of {id}')
                self._current_item = id
            else:
                distance = distance_from_point_to_rectangle((x, y), self.coords(id))
                print(distance)
                if distance <= 15:
                    self._current_item = id
                else:
                    self._current_item = None

        print(f'After manipulations: {self._current_item}')
        if self._current_item and self.checkInPoints(event.x, event.y) is not None:
            self._current_point = self.checkInPoints(event.x, event.y)
            self.previous = (self.canvasx(event.x), self.canvasy(event.y))
            self._current_item = self._previous_item
            self.bind('<B1-Motion>', self.resize)
            self.bind('<Motion>', self.updateCursor)

            return

        elif self._current_item and self._current_item == self._previous_item:
            self.previous = (self.canvasx(event.x), self.canvasy(event.y))
            self.moveItem(event)
            self.bind('<B1-Motion>', self.moveItem)
            return

        self.unbind('<Motion>')

        if self._current_item and self._current_item == self._current_resize_rect:
            self._current_item = self.find_enclosed(*self.bbox(self._current_resize_rect))[0]

        # if self._current_item and not self.check_in_bbox(self._current_item, event.x, event.y):
        #     self._current_item = None

        if self._current_item is None:
            self.removeRect()
            return

        if self._current_item != self._previous_item:
            self.removeRect()
            self.addRect()
            self.bind('<Motion>', self.updateCursor)

    def updateCursor(self, event):  # method that updates cursor when hovering over resize points

        point = self.checkInPoints(event.x, event.y)

        if point:
            key = list(self.resizePoints.keys())[list(self.resizePoints.values()).index(point)]
            self.config(cursor=self.cursors[key])

        else:
            self.config(cursor='')

    def checkInPoints(self, x, y):  # checks if the mouse is over the resizePoints
        for item in self.resizePoints.values():
            if self.check_in_bbox(item, x, y):
                return item

        return None

    def addRect(self):  # adds a rect around the canvas item

        bbox = self.bbox(self._current_item)

        if bbox:
            self._current_resize_rect = self.create_rectangle(bbox, tags=(self._tag,))  # draws rectangle

            # the below are the points at 4 corners of resize rect
            self.resizePoints[self.TOP_LEFT] = self.create_oval(bbox[0] - 5, bbox[1] - 5, bbox[0] + 5, bbox[1] + 5,
                                                                tags=(self._tag,), fill='#000000')
            self.resizePoints[self.TOP_RIGHT] = self.create_oval(bbox[2] - 5, bbox[1] - 5, bbox[2] + 5, bbox[1] + 5,
                                                                 tags=(self._tag,), fill='#000000')
            self.resizePoints[self.BOTTOM_RIGHT] = self.create_oval(bbox[2] - 5, bbox[3] - 5, bbox[2] + 5, bbox[3] + 5,
                                                                    tags=(self._tag,), fill='#000000')
            self.resizePoints[self.BOTTOM_LEFT] = self.create_oval(bbox[0] - 5, bbox[3] - 5, bbox[0] + 5, bbox[3] + 5,
                                                                   tags=(self._tag,), fill='#000000')

    def removeRect(self):  # removes thre resize rectangle
        for x in self.find_withtag(self._tag):
            self.delete(x)

        self.resizePoints = {}
        self._current_resize_rect = None

    def check_in_bbox(self, item, x, y):  # checks if (x, y) points are inside the bounding box
        box = self.bbox(item)
        return box[0] < x < box[2] and box[1] < y < box[3]

    def moveItem(self, event):  # moves the canvas item

        xc, yc = self.canvasx(event.x), self.canvasy(event.y)
        self._bboxes.delete(self._current_item, self.coords(self._current_item))
        print(f'MOVE: Before: {self.coords(self._current_item)}')
        self.move(self._current_item, xc - self.previous[0], yc - self.previous[1])
        print(f'MOVE: After: {self.coords(self._current_item)}')
        self._bboxes.insert(self._current_item, self.coords(self._current_item))
        self.updateResizeRect()

        self.previous = (xc, yc)

    def updateResizeRect(self):  # updates the position of the resize rectangle

        self.coords(self._current_resize_rect, *self.bbox(self._current_item))
        new_coord = self.coords(self._current_resize_rect)

        # note: depending on your tkinter version moveto might not be available. So use the .coords method
        # eg: coords(self.resizePoints[self.TOP_LEFT], new_coords[0]-5, new_coords[1]-5, new_coords[0]+5,new_coords[1]+5)
        # check how the coords are assigned in the addRect method and adjust accordingly if your tkinter version does't have `moveto`

        self.moveto(self.resizePoints[self.TOP_LEFT], new_coord[0] - 5, new_coord[1] - 5)
        self.moveto(self.resizePoints[self.TOP_RIGHT], new_coord[2] - 5, new_coord[1] - 5)
        self.moveto(self.resizePoints[self.BOTTOM_RIGHT], new_coord[2] - 5, new_coord[3] - 5)
        self.moveto(self.resizePoints[self.BOTTOM_LEFT], new_coord[0] - 5, new_coord[3] - 5)

    def resize(self, event):  # resizes the canvas item
        item_coords = self.coords(self._current_item)
        print(f'RESIZE: BEFORE: {self.coords(self._current_item)}')
        self._bboxes.delete(self._current_item, item_coords)
        item_bbox = self.bbox(self._current_item)
        try:

            if self.resizePoints[self.TOP_LEFT] == self._current_point:
                self.coords(self._current_item, event.x, event.y, item_coords[2], item_coords[3])
                # self.scale(self._current_item, item_coords[0], item_coords[1], 2, 2)

            elif self.resizePoints[self.TOP_RIGHT] == self._current_point:
                self.coords(self._current_item, item_coords[0], event.y, event.x, item_coords[3])


            elif self.resizePoints[self.BOTTOM_RIGHT] == self._current_point:
                self.coords(self._current_item, item_coords[0], item_coords[1], event.x, event.y)


            elif self.resizePoints[self.BOTTOM_LEFT] == self._current_point:
                self.coords(self._current_item, event.x, item_coords[1], item_coords[2], event.y)

        except (TclError, IndexError):

            font = self.itemcget(self._current_item, 'font')
            new_font = Font(font=font)

            increase = math.sqrt(
                (event.y - self.previous[1]) ** 2 + (event.x - self.previous[0]) ** 2)  # + new_font.actual()['size']

            if not (self.previous[0] < event.x and self.previous[1] < event.y):
                increase = - increase

            new_font.configure(size=int(increase))
            self.itemconfigure(self._current_item, font=new_font)

        self._bboxes.insert(self._current_item, self.coords(self._current_item))
        print(f'RESIZE: AFTER: {self.coords(self._current_item)}')
        self.updateResizeRect()


if __name__ == '__main__':
    root = tk.Tk()

    canvas = Canvas(root)
    canvas.pack(fill='both', expand=True)

    canvas.create_line(10, 50, 100, 200)

    canvas.create_rectangle(120, 50, 180, 200)
    canvas.create_oval(200, 50, 400, 200)

    # canvas.create_line(55, 85, 155, 85, 105, 180, 55, 85)

    canvas.create_text(100, 150, text='HELLO', font=("Comic Sans MS", 20, "italic"))

    root.mainloop()
