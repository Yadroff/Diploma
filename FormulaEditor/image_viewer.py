from tkinter import Tk, Frame, Menu


class MainWindow(Frame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def open_file(self):
        pass

    def initUI(self):
        self.master.title('Title')

        menu_bar = Menu(self.master)
        self.master.config(menu=menu_bar)

        file_menu = Menu(menu_bar)
        file_menu.add_command(label='Open', command=self.open_file)
        menu_bar.add_cascade(label='File', menu=file_menu)


def main():
    root = Tk()
    root.geometry('400x300+300+300')
    app = MainWindow()
    root.mainloop()


if __name__ == '__main__':
    main()
