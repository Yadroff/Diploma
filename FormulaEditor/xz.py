from tkinter import *
from tkinter import ttk

root = Tk()
root.title("METANIT.COM")
root.geometry("250x200")

h = ttk.Scrollbar(orient=HORIZONTAL)
v = ttk.Scrollbar(orient=VERTICAL)
canvas = Canvas(scrollregion=(0, 0, 1000, 1000), bg="white", yscrollcommand=v.set, xscrollcommand=h.set)
h["command"] = canvas.xview
v["command"] = canvas.yview

canvas.grid(column=0, row=0, sticky=(N, W, E, S))
h.grid(column=0, row=1, sticky=(W, E))
v.grid(column=1, row=0, sticky=(N, S))
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

canvas.create_rectangle(10, 10, 300, 300, fill="red")

root.mainloop()