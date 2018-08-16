import tkinter as Tk
import tkinter.ttk as ttk
import magic2gui.callbacks as m2callbacks
import magic2gui.matplotlib_frame as m2mframe
import magic2gui.status_bar as m2status_bar
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
        self.status = None


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
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    mframe.grid(row=0, column=0, sticky=("N", "S", "E", "W"))
    options.fig = mframe.fig
    options.ax = mframe.ax
    options.ax.imshow(imread('logo.png'))

    display_group = Tk.LabelFrame(root, text="Display", padx=5, pady=5)
    display_group.grid(row=0, column=1, padx=5, pady=5, sticky="N")

    b = ttk.Button(display_group, text="showerror", command=lambda:
        print("button"))
    b.pack()

    options.status = m2status_bar.StatusBar(root)
    options.status.grid(row=1, columnspan=2, sticky=("W", "E"))
    # status.set("waiting",-1)

    root.mainloop()


if __name__ == "__main__":
    main()
