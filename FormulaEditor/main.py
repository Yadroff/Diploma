import tkinter as tk
from tkinter import *

from tkinter import filedialog, Menu
from PIL import Image, ImageTk
import rtree

import time
import csv

import canvas


def load_bboxes(bbox_file):
    bboxes = []
    with open(bbox_file, 'r', newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=' ')
        for row in reader:
            x_min, y_min, x_max, y_max = map(float, row[1:])
            bboxes.append([x_min, y_min, x_max, y_max])
    return bboxes


class ImageViewer(tk.Frame):
    MIN_DELTA_BETWEEN_RELEASE = 0.01

    def __init__(self, master=None):
        super().__init__(master)
        self.temp_rect = None
        self.left_button_pressed_time = None
        self.selected_bbox_id = None
        self.image_id = None
        self.scrollbar_y = None
        self.scrollbar_x = None
        self.scroll_canvas = None
        self.image_tk = None
        self.btn_open = None
        self.toolbar = None
        self.master = master
        self.master.title('Image Viewer')
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self._create_menu()
        self.bboxes_tree = rtree.Index()
        self.bboxes = []
        # self.scroll_canvas.bind("<Button-1>", self.button_pressed)
        # self.scroll_canvas.bind("<ButtonRelease-1>", self.button_released)
        # self.scroll_canvas.bind("<B1-Motion>", self.button_moved)
        # if master:
        #     master.bind("<BackSpace>", self.delete_pressed)
        # else:
        #     self.bind("<BackSpace>", self.delete_pressed)

    def create_widgets(self):
        self.scrollbar_x = tk.Scrollbar(self, orient='horizontal')
        self.scrollbar_y = tk.Scrollbar(self, orient='vertical')

        self.scroll_canvas = canvas.Canvas(self, scrollregion=(0, 0, 1000, 1000),
                                       yscrollcommand=self.scrollbar_y.set,
                                       xscrollcommand=self.scrollbar_x.set)

        self.scrollbar_x['command'] = self.scroll_canvas.xview
        self.scrollbar_y['command'] = self.scroll_canvas.yview

        self.scroll_canvas.grid(column=0, row=0, sticky=(N, W, E, S))
        self.scrollbar_x.grid(column=0, row=1, sticky=(W, E))
        self.scrollbar_y.grid(column=1, row=0, sticky=(N, S))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll_canvas.bind('<Configure>',
                                lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))

        self.toolbar = tk.Frame(self.master, bd=1, relief=tk.RAISED)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_open = tk.Button(self.toolbar, text='Done', command=self.open_image)
        self.btn_open.pack(side=tk.LEFT, padx=2, pady=2)

    def _create_menu(self):
        self.menu_bar = Menu(self.master)
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.open_image)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.master.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.master.config(menu=self.menu_bar)

    def open_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")])
        if not filepath:
            return

        image = Image.open(filepath)
        self.scroll_canvas.configure(scrollregion=(0, 0, image.width, image.height))
        self.image_tk = ImageTk.PhotoImage(image)

        self.scroll_canvas.delete("IMG")
        self.image_id = self.scroll_canvas.create_image(0, 0, anchor='nw', image=self.image_tk, tags="IMG")
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        self.fill_bboxes('test.txt')

    def fill_bboxes(self, filename):
        bboxes = load_bboxes(filename)
        for i, bbox in enumerate(bboxes):
            self.bboxes_tree.insert(id=i, coordinates=bbox)
            rect_id = self.scroll_canvas.create_rectangle(bbox, outline='red', width=3)
            self.bboxes.append(rect_id)
            # self.scroll_canvas.tag_bind(rect_id, "<Button-1>", self.on_pressed_rect)
            # self.scroll_canvas.tag_bind(rect_id, "<ButtonRelease-1>", self.on_released_rect)
            # self.scroll_canvas.tag_bind(rect_id, "<B1-Motion>", self.on_moved_rect)
            # self.scroll_canvas.tag_bind(rect_id, "<BackSpace>", self.on_delete_rect)

    def button_pressed(self, event):
        print('Pressed event')
        print(f'Canvas Y(0): {self.scroll_canvas.canvasy(0)}')
        x, y = self.scroll_canvas.canvasx(event.x), self.scroll_canvas.canvasy(event.y)
        intersected = list(self.bboxes_tree.intersection((x - 5, y - 5, x + 5, y + 5)))
        print(list(self.bboxes_tree.nearest((x, y), 1)))
        print(x, y)
        if len(intersected):
            self.selected_bbox_id = intersected[0]
            self.left_button_pressed_time = time.perf_counter()
        else:
            self.selected_bbox_id = None
            self.left_button_pressed_time = None

    def button_released(self, event):
        if self.selected_bbox_id:
            print('Released event')
            released_time = time.perf_counter()
            if self.left_button_pressed_time and released_time - self.left_button_pressed_time >= self.MIN_DELTA_BETWEEN_RELEASE:
                print(list(self.bboxes_tree.intersection((event.x - 15, event.y - 15, event.x + 15, event.y + 15))))
                print(list(self.bboxes_tree.nearest((event.x, event.y), 1)))

    def button_moved(self, event):
        print('Moved event')
        if self.selected_bbox_id:
            # self.scroll_canvas.delete(self.bboxes[self.selected_bbox_id])
            # self.bboxes[self.selected_bbox_id] = self.scroll_canvas.create_rectangle()
            print(list(self.bboxes_tree.intersection((event.x - 15, event.y - 15, event.x + 15, event.y + 15))))
            print(list(self.bboxes_tree.nearest((event.x, event.y), 1)))

    def delete_pressed(self, event):
        print('Pressed event')
        print(self.selected_bbox_id)
        if self.selected_bbox_id is not None:
            print(self.bboxes[self.selected_bbox_id])
            # self.bboxes_tree.delete(self.selected_bbox_id)
            self.scroll_canvas.delete(self.bboxes[self.selected_bbox_id])
            self.bboxes[self.selected_bbox_id] = None
            self.selected_bbox_id = None

    def on_pressed_rect(self, event):
        x, y = self.scroll_canvas.canvasx(event.x), self.scroll_canvas.canvasy(event.y)
        id = event.widget.find_overlapping(x - 3, y - 3, x + 3, y + 3)
        print('Nearest: ', list(self.bboxes_tree.nearest((x - 3, y - 3, x + 3, y + 3), 1)))
        id = list(self.bboxes_tree.nearest(((x - 3, y - 3, x + 3, y + 3)), 1))[0]
        print(f'Rect enter: {id}. {self.scroll_canvas.coords(id)}')
        self.selected_bbox_id = id

    def on_moved_rect(self, event):
        if self.temp_rect:
            self.scroll_canvas.delete(self.temp_rect)
        x, y = self.scroll_canvas.canvasx(event.x), self.scroll_canvas.canvasy(event.y)
        left, top, right, bottom = self.scroll_canvas.coords(self.selected_bbox_id)
        width_2 = (right - left) / 2
        height_2 = (bottom - top) / 2
        self.temp_rect = self.scroll_canvas.create_rectangle(x - width_2, y - height_2, x + width_2, y + width_2,
                                                             outline="blue", width=3, dash=3)

    def on_released_rect(self, event):
        if not self.temp_rect:
            return
        self.scroll_canvas.delete(self.temp_rect)
        x, y = self.scroll_canvas.canvasx(event.x), self.scroll_canvas.canvasy(event.y)
        left, top, right, bottom = self.scroll_canvas.coords(self.selected_bbox_id)
        width_2 = (right - left) / 2
        height_2 = (bottom - top) / 2
        self.temp_rect = self.scroll_canvas.create_rectangle(x - width_2, y - height_2, x + width_2, y + width_2,
                                                             outline="red", width=3)

    def on_delete_rect(self, event):
        id = event.widget.find_closest(event.x, event.y)
        print(f'Rect leave: {id}. {self.scroll_canvas.coords(id)}')
        self.scroll_canvas.delete(id)
        self.bboxes.remove(id)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewer(master=root)
    app.mainloop()
