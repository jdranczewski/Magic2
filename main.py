import tkinter as Tk
import magic2gui.callbacks as m2callbacks
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2TkAgg)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.pyplot import imread
import numpy as np


class Options:
    def __init__(self):
        self.objects = {
            "background": {},
            "plasma": {}
        }
        self.fig = None
        self.ax = None


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
                         m2callbacks.open_background_image(options, imshow))

    options.fig = fig = Figure(figsize=(5, 4), dpi=100)
    options.ax = ax = fig.add_subplot(111)
    imshow = ax.imshow(imread('logo.png'))
    canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    toolbar = NavigationToolbar2TkAgg(canvas, root)
    toolbar.update()
    canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    def on_key_press(event):
        pass

    canvas.mpl_connect("key_press_event", on_key_press)

    root.mainloop()


if __name__ == "__main__":
    main()
