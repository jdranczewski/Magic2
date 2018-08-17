import tkinter as Tk
import tkinter.ttk as ttk
import magic2gui.callbacks as m2callbacks
import magic2gui.matplotlib_frame as m2mframe
import magic2gui.status_bar as m2status_bar
from matplotlib.pyplot import imread
import numpy as np
import pickle


# This is a way of getting global variables without actually using global
# variables, which would be messy. There is a single Options object for the
# entire application and it stores stuff, from Canvas and Fringes objects,
# to settings, matplotlib objects and tkinter variables.
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
        # matplotlib's objects used to manipulate the main graph
        self.fig = None
        self.ax = None
        # A Labeller object. Its existence is an indication of being in
        # labelling mode and having to disattach event listeners when
        # switching the graph display
        self.labeller = None
        # The status bar
        self.status = None
        # The tkinter variable associated with radio buttons that decide
        # which graph to show. It updates automatically when the radios are
        # clicked, and the radios update when the variable is set
        self.show_var = None
        # mode is a variable storing the state in which the programme is,
        # like background_fringes
        self.mode = None
        # An image of the two interpolations subtracted
        self.subtracted = None


def main():
    # Create a root tkinter object and set its title
    root = Tk.Tk()
    root.wm_title("Magic2")
    # Set the first row and column in root's grid layout to resize.
    # This way the graph will fit all the available space
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    # Create an Options object for storing settings and other objects
    options = Options()

    # Create the menu
    menu = Tk.Menu(root)
    root.config(menu=menu)
    # Create the file submenu
    filemenu = Tk.Menu(menu)
    menu.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open background image",
                         command=lambda:
                         m2callbacks.open_image(options, 'background'))
    filemenu.add_command(label="Open plasma image",
                         command=lambda:
                         m2callbacks.open_image(options, 'plasma'))

    # Create the matplotlib widget
    options.mframe = m2mframe.GraphFrame(root, bind_keys=True, show_toolbar=True)
    # The sticky parameter makes the graph fill the whole grid cell
    options.mframe.grid(row=0, column=0, sticky=("N", "S", "E", "W"))
    # Get matplotlib's Figure and Axes for the graph
    options.fig = options.mframe.fig
    options.ax = options.mframe.ax
    # Show a placeholder image
    options.ax.imshow(imread('logo.png'))

    # Create the side menu
    side_frame = Tk.Frame(root)
    side_frame.grid(row=0, column=1, padx=5, pady=5, sticky="N")
    # Create a group for display options
    display_group = Tk.LabelFrame(side_frame, text="Display", padx=5, pady=5)
    display_group.pack(fill=Tk.BOTH)
    # Create radio buttons for display modes
    display_modes = [
        ("Background fringes", "background_fringes"),
        ("Background map", "background_map"),
        ("Plasma fringes", "plasma_fringes"),
        ("Plasma map", "plasma_map"),
        ("Subtracted map", "subtracted_graph"),
        ("Plasma density", "phase_graph")
    ]
    options.show_var = Tk.StringVar()
    for name, key in display_modes:
        b = ttk.Radiobutton(display_group, text=name, variable=options.show_var,
                            value=key, command=lambda: m2callbacks.show_radio(options))
        b.pack(anchor=Tk.W)
    # create a group for operations that can be performed
    operations_group = Tk.LabelFrame(side_frame, text="Operations", padx=5, pady=5)
    operations_group.pack(fill=Tk.BOTH)
    b = ttk.Button(operations_group, text="Interpolate",
                   command=lambda: m2callbacks.interpolate(options))
    b.pack()
    b = ttk.Button(operations_group, text="Subtract",
                   command=lambda: m2callbacks.subtract(options))
    b.pack()
    def make_pickle():
        print("Making pickle")
        pickle.dump(options.objects, open("save.p", "wb"))
    b = ttk.Button(operations_group, text="Pickle",
                   command=make_pickle)
    b.pack()
    def unpickle():
        options.objects = pickle.load(open("save.p", "rb"))
        print("Opened")
    b = ttk.Button(operations_group, text="Unpickle",
                   command=unpickle)
    b.pack()

    # Create a status bar and place it at the bottom of the window.
    options.status = m2status_bar.StatusBar(root)
    options.status.grid(row=1, columnspan=2, sticky=("W", "E"))
    # status.set("waiting",-1)

    # Start the programme's main loop
    root.mainloop()


if __name__ == "__main__":
    main()
