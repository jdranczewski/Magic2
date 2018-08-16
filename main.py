import tkinter as Tk
import magic2gui.callbacks as m2callbacks
import magic2gui.matplotlib_frame as m2mframe
from matplotlib.pyplot import imread
import numpy as np


class Options:
    def __init__(self):
        self.objects = {
            "background": {
                "canvas": None,
                "fringes": None
            },
            "plasma": {
                "canvas": None,
                "fringes": None
            }
        }
        self.fig = None
        self.ax = None
        self.labeller = None


def main():
    root = Tk.Tk()
    root.wm_title("Magic2")
    options = Options()

    menu = Tk.Menu(root)
    root.config(menu=menu)

    filemenu = Tk.Menu(menu)
    menu.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open background image",
                         command=lambda:
                         m2callbacks.open_image(options, 'background'))

    mframe = m2mframe.GraphFrame(root, show_toolbar=True)
    mframe.pack(fill=Tk.BOTH, expand=1)
    options.fig = mframe.fig
    options.ax = mframe.ax
    options.ax.imshow(imread('logo.png'))

    b = Tk.Button(root, text="showerror", command=lambda:
        print("button"))
    b.pack(side=Tk.RIGHT)

    root.mainloop()


if __name__ == "__main__":
    main()
