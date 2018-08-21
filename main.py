import tkinter as Tk
import tkinter.ttk as ttk
import magic2.graphics as m2graphics
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
        # tkinter's root
        self.root = None
        # matplotlib's objects used to manipulate the main graph
        self.fig = None
        self.ax = None
        self.imshow = None
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
        # Colormap setting for matplotlib
        self.cmap = m2graphics.cmap
        # An image of the two interpolations subtracted
        self.subtracted = None
        # The colorbar
        self.cbar = None
        # Shot properties
        self.resolution = None
        self.depth = None
        self.wavelength = None
        self.double = None


def main():
    # Create an Options object for storing settings and other objects
    options = Options()
    # Create a root tkinter object and set its title
    options.root = root = Tk.Tk()
    root.wm_title("Magic2")
    # Set the first row and column in root's grid layout to resize.
    # This way the graph will fit all the available space
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

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
    filemenu.add_separator()
    def make_pickle():
        print("Making pickle")
        pickle.dump(options.objects, open("save.p", "wb"))
    filemenu.add_command(label="Pickle", command=make_pickle)
    def unpickle():
        options.objects = pickle.load(open("save.p", "rb"))
        print("Opened")
    filemenu.add_command(label="Unpickle", command=unpickle)
    filemenu.add_separator()
    filemenu.add_command(label="Export the current view's data",
                         command=lambda:
                         m2callbacks.export(options))
    filemenu.add_command(label="Save the graph as an image",
                         command=lambda:
                         m2callbacks.export_image(options))
    # Create the process submenu
    processmenu = Tk.Menu(menu)
    menu.add_cascade(label="Process", menu=processmenu)
    processmenu.add_command(label="Exact interpolation",
                            command=lambda:
                            m2callbacks.interpolate_exact(options))
    processmenu.add_command(label="Fast interpolation",
                            command=lambda:
                            m2callbacks.interpolate_fast(options))
    processmenu.add_command(label="Exact interpolation (debug mode)",
                            command=lambda:
                            m2callbacks.interpolate_debug(options))
    processmenu.add_separator()
    processmenu.add_command(label="Subtract",
                            command=lambda:
                            m2callbacks.subtract(options))
    processmenu.add_separator()
    processmenu.add_command(label="Calculate plasma density",
                            command=lambda:
                            m2callbacks.plasma_density(options))
    processmenu.add_command(label="Set shot details",
                            command=lambda:
                            m2callbacks.shot_options(options))
    processmenu.add_separator()
    processmenu.add_command(label="Cosine",
                            command=lambda:
                            m2callbacks.cosine(options))
    # Create the display submenu
    displaymenu = Tk.Menu(menu)
    menu.add_cascade(label="Display", menu=displaymenu)
    displaymenu.add_command(label="Set colormap",
                            command=lambda:
                            m2callbacks.set_colormap(options))

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
    width_frame = Tk.Frame(display_group)
    width_frame.pack()
    b = Tk.Button(width_frame, text="<", command=lambda: m2callbacks.lower_width(options))
    b.pack(side=Tk.LEFT)
    l = Tk.Label(width_frame, text="width:")
    l.pack(side=Tk.LEFT)
    options.width_var = Tk.IntVar()
    options.width_var.set(2)
    l = Tk.Label(width_frame, textvar=options.width_var)
    l.pack(side=Tk.LEFT)
    b = Tk.Button(width_frame, text=">", command=lambda: m2callbacks.higher_width(options))
    b.pack(side=Tk.LEFT)

    # Create a group for labelling options
    direction_group = Tk.LabelFrame(side_frame, text="Labelling", padx=5, pady=5)
    direction_group.pack(fill=Tk.BOTH)
    # Create radio buttons for display modes
    display_modes = [
        ("Increasing phase", 1),
        ("Constant phase", 0),
        ("Decreasing phase", -1),
    ]
    options.direction_var = Tk.IntVar()
    options.direction_var.set(1)
    for name, key in display_modes:
        b = ttk.Radiobutton(direction_group, text=name,
                            variable=options.direction_var, value=key,
                            command=lambda: options.mframe.canvas._tkcanvas.focus_set())
        b.pack(anchor=Tk.W)

    # Create a status bar and place it at the bottom of the window.
    options.status = m2status_bar.StatusBar(root)
    options.status.grid(row=1, columnspan=2, sticky=("W", "E"))
    # status.set("waiting",-1)

    # Start the programme's main loop
    root.mainloop()


if __name__ == "__main__":
    main()
