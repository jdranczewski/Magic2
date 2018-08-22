import tkinter.filedialog as fd
import tkinter.messagebox as mb
import tkinter as Tk
import tkinter.ttk as ttk
import scipy as sp
from copy import copy
from matplotlib.pyplot import cm

import magic2gui.dialog as m2dialog
import magic2.graphics as m2graphics
import magic2.fringes as m2fringes
import magic2.labelling as m2labelling
import magic2.triangulate as m2triangulate


# Open and image for either the background or foreground fringes
def open_image(options, env):
    if options.objects[env]['canvas'] is not None and not mb.askokcancel(
        "Overwrite?", "There is a " + env
        + "file open already. Opening a new one will "
        + "overwrite all changes made to it!"
    ):
        pass
    else:
        # Display a window for chooisng the file
        filename = fd.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")])
        if filename is not None:
            options.status.set("Reading the file", 0)
            # Delete the old objects if we are overwriting
            if options.objects[env]['canvas'] is not None:
                del options.objects[env]['canvas']
                del options.objects[env]['fringes']
                del options.subtracted
                options.subtracted = None
            # Create a canvas object
            canvas = options.objects[env]['canvas'] = m2graphics.Canvas(filename)
            options.status.set("Looking for fringes", 33)
            # Extract fringe information from the file
            fringes = options.objects[env]['fringes'] = m2fringes.Fringes()
            m2fringes.read_fringes(fringes, canvas)
            options.status.set("Rendering fringes", 66)
            # Render the fringes onto the canvas
            m2graphics.render_fringes(fringes, canvas, width=options.width_var.get())
            # Set the mode (the set_mode function handles rendering)
            options.mode = env + "_fringes"
            set_mode(options)
            options.status.set("Done", 100)


def export(options):
    if options.mode is not None:
        filename = fd.asksaveasfilename(filetypes=[(".csv file", "*.csv"),
                                                   ("All files", "*")],
                                        defaultextension=".csv")
        if filename != '':
            options.status.set("Exporting", 0)
            if options.mode.split("_")[1] == 'fringes':
                sp.savetxt(filename, sp.ma.filled(options.objects[options.mode.split("_")[0]]['canvas'].fringe_phases,fill_value=-1024), delimiter=",")
            else:
                sp.savetxt(filename, sp.ma.filled(options.imshow.get_array(),fill_value=-1024), delimiter=",")
            options.status.set("Done", 100)
    else:
        mb.showinfo("No mode chosen", "Please choose one of the display modes from the menu on the right!")


class DpiDialog(m2dialog.Dialog):
    def body(self, master):
        ttk.Label(master, text="DPI:").grid(row=0)
        self.e = ttk.Entry(master)
        self.e.insert(0, 300)
        self.e.grid(row=0, column=1)
        return self.e

    def validate(self):
        try:
            int(self.e.get())
            return 1
        except ValueError:
            mb.showerror("Error", "The value needs to be an integer!")
            return 0

    def apply(self):
        self.result = int(self.e.get())


def export_image(options):
    dialog = DpiDialog(options.root, title="Choose quality")
    if dialog.result is not None:
        filename = fd.asksaveasfilename(filetypes=[("PNG files", "*.png;*.PNG"),
                                                   ("All files", "*")],
                                        defaultextension=".png")
        if filename != '':
            options.fig.savefig(filename, dpi=dialog.result)


class CmapDialog(m2dialog.Dialog):
    def __init__(self, parent, options, title=None):
        self.options = options
        m2dialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        ttk.Label(master, text="Colormap:").grid(row=0)
        self.var = Tk.StringVar(master)
        choice = ('--perceptually uniform--', 'plasma', 'viridis', 'inferno',
                  'magma', '--the classic--', 'jet', '--sequnetial--',
                  'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                  'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                  'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
                  'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
                  'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
                  'hot', 'afmhot', 'gist_heat', 'copper', '--misc--', 'ocean',
                  'gist_earth', 'terrain', 'gist_stern', 'gnuplot',
                  'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'hsv',
                  'gist_rainbow', 'rainbow', 'nipy_spectral', 'gist_ncar')
        self.e = ttk.OptionMenu(master, self.var, self.options.cmap.name, *choice)
        self.e.grid(row=0, column=1)
        return self.e

    def validate(self):
        if self.var.get()[:2] != "--":
            return 1
        else:
            mb.showerror("Error", "Choose a valid colormap.")
            return 0

    def apply(self):
        self.result = self.var.get()


def set_colormap(options):
    dialog = CmapDialog(options.root, options)
    if dialog.result is not None:
        options.cmap = copy(cm.get_cmap(dialog.result))
        # White is for masking
        options.cmap.set_bad('white', 1.0)
        # Black is for unlabelled fringes
        options.cmap.set_under('black', 1.0)
        if options.mode is not None:
            set_mode(options)


# Handle the user choosing one of the radio buttons
def show_radio(options):
    # Give the focus back to the graph
    options.mframe.canvas._tkcanvas.focus_set()
    # Store the mode info from the buttons
    key = options.show_var.get().split("_")
    # Set the buttons to the previous state, in case the user cancels
    options.show_var.set(options.mode)
    if key[0] == 'background' or key[0] == 'plasma':
        # If the fringe image has not been loaded yet, open one
        if options.objects[key[0]]['canvas'] is None:
            open_image(options, key[0])
        # If the user wants fringes, show them
        elif key[1] == 'fringes':
            options.mode = "_".join(key)
            set_mode(options)
        # If the user wants the interpolated map, check if it exists...
        elif key[1] == 'map':
            if options.objects[key[0]]['canvas'].interpolation_done:
                options.mode = "_".join(key)
                set_mode(options)
            # ...if not, give the user the option to generate one
            else:
                ans = mb.askyesnocancel("Fast or exact?", "Would you like to remove flat triangles from the triangulation that is used when interpolating? This is slower, but more exact.")
                if ans:
                    interpolate_exact(options, key[0])
                elif ans is not None:
                    interpolate_fast(options, key[0])

    # If the user wants the subtracted map, show it or calculate it and show it
    # (the calculation is a quick process, so it doesn't make sense to ask
    # the user for permission)
    elif key[0] == 'subtracted':
        if options.subtracted is None:
            print("Performing")
            subtract(options)
        else:
            options.mode = "_".join(key)
            set_mode(options)
    elif key[0] == 'density':
        if options.density is None:
            print("Perf")
            plasma_density(options)
        else:
            options.mode = "_".join(key)
            set_mode(options)


# Render the correct image on the graph's canvas
def set_mode(options):
    key = options.mode.split("_")
    # Clear the axes and all labellers/event handlers attached to them
    # (if they exist)
    options.ax.clear()
    if options.labeller is not None:
        m2labelling.stop_labelling(options.fig, options.labeller)
    if options.cbar is not None:
        # The whole figure is cleaned, as simply deleting the colorbar
        # resulted in the graph being shifted to the right
        options.mframe.cax.clear()
        options.mframe.cax.axis('off')
        # options.ax = options.fig.add_subplot(111)
        # options.cbar.remove()
        options.cbar = None
    if key[1] == 'fringes':
        canvas = options.objects[key[0]]['canvas']
        fringes = options.objects[key[0]]['fringes']
        # The fringes image is masked where there is no data
        options.imshow = canvas.imshow = options.ax.imshow(
            sp.ma.masked_where(canvas.fringe_phases_visual == -1024,
                               canvas.fringe_phases_visual),
            cmap=options.cmap
        )
        canvas.imshow.set_clim(fringes.min, fringes.max)
        options.labeller = m2labelling.label(fringes, canvas,
                                             options.fig, options.ax,
                                             options)
    elif key[1] == 'map':
        canvas = options.objects[key[0]]['canvas']
        # The map image is masked where there is no interpolation data and
        # on the user-defined mask
        options.imshow = canvas.imshow = options.ax.imshow(
            sp.ma.masked_where(sp.logical_or(canvas.mask == False, canvas.interpolated == -1024.0),
                               canvas.interpolated),
            cmap=options.cmap
        )
    elif key[0] == 'subtracted':
        # Show the subtracted image
        # note: this function works on the assumption that the things it is
        # attempting to show have been generated previously. It is the burden
        # of event handlers to check whether this is corrct
        options.imshow = options.ax.imshow(options.subtracted, cmap=options.cmap)
        options.cbar = options.fig.colorbar(options.imshow, cax=options.mframe.cax)
        options.mframe.cax.axis('on')
        options.cbar.ax.set_ylabel('Fringe shift', rotation=270)
    elif key[0] == 'density':
        options.imshow = options.ax.imshow(options.density, cmap=options.cmap)
        options.cbar = options.fig.colorbar(options.imshow, cax=options.mframe.cax)
        options.mframe.cax.axis('on')
        options.cbar.ax.set_ylabel('Electron density / $m^{-3}$', labelpad=20)
    # Refresh the graph's canvas
    options.fig.canvas.draw()
    # Set the radio buttons to the correct position
    options.show_var.set(options.mode)


def lower_width(options):
    if options.mode is None or options.mode.split("_")[1] != "fringes":
        mb.showinfo("Not in fringe display mode", "You need to be in a fringe display mode to change the width setting.")
    else:
        if options.width_var.get() > 0:
            options.width_var.set(options.width_var.get() - 1)
            if options.objects['background']['canvas'] is not None:
                m2graphics.clear_visual(options.objects['background']['canvas'])
                m2graphics.render_fringes(options.objects['background']['fringes'], options.objects['background']['canvas'], width=options.width_var.get())
            if options.objects['plasma']['canvas'] is not None:
                m2graphics.clear_visual(options.objects['plasma']['canvas'])
                m2graphics.render_fringes(options.objects['plasma']['fringes'], options.objects['plasma']['canvas'], width=options.width_var.get())
            set_mode(options)

def higher_width(options):
    if options.mode is None or options.mode.split("_")[1] != "fringes":
        mb.showinfo("Not in fringe display mode", "You need to be in a fringe display mode to change the width setting.")
    else:
        options.width_var.set(options.width_var.get() + 1)
        if options.objects['background']['canvas'] is not None:
            m2graphics.render_fringes(options.objects['background']['fringes'], options.objects['background']['canvas'], width=options.width_var.get())
        if options.objects['plasma']['canvas'] is not None:
            m2graphics.render_fringes(options.objects['plasma']['fringes'], options.objects['plasma']['canvas'], width=options.width_var.get())
        set_mode(options)


# This performs some checks and then starts off the triangulation for
# either the background or plasma fringes, depending on which one is
# currently displayed
def interpolate_exact(options, env=None):
    if options.mode is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    elif options.mode.split("_")[0] != 'plasma' and options.mode.split("_")[0] != 'background':
        mb.showinfo("No mode chosen", "Please choose either the background or plasma display mode from the menu on the right!")
    else:
        # If the above checks are passed, perform the triangulation and let
        # set_mode render it
        if env is None:
            env = options.mode.split("_")[0]
        tri = m2triangulate.triangulate(options.objects[env]['canvas'],
                                        options.ax, options.status)
        if tri is None:
            mb.showerror("Triangulation failed", "No points detected, so the triangulation failed. Have you labelled the fringes?")
        else:
            options.mode = env + "_map"
            set_mode(options)


def interpolate_fast(options, env=None):
    if options.mode is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    elif options.mode.split("_")[0] != 'plasma' and options.mode.split("_")[0] != 'background':
        mb.showinfo("No mode chosen", "Please choose either the background or plasma display mode from the menu on the right!")
    else:
        # If the above checks are passed, perform the triangulation and let
        # set_mode render it
        if env is None:
            env = options.mode.split("_")[0]
        tri = m2triangulate.fast_tri(options.objects[env]['canvas'],
                                     options.ax, options.status)
        if tri is None:
            mb.showerror("Triangulation failed", "No points detected, so the triangulation failed. Have you labelled the fringes?")
        else:
            options.mode = env + "_map"
            set_mode(options)


def interpolate_debug(options, env=None):
    if options.mode is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    elif options.mode.split("_")[0] != 'plasma' and options.mode.split("_")[0] != 'background':
        mb.showinfo("No mode chosen", "Please choose either the background or plasma display mode from the menu on the right!")
    elif mb.askokcancel("Debug triangulation", "You are about to perform a debug mode interpolation. This shows the output of every step in a separate graph window. Flat triangles are usually highlighted green. Look for error messages and progress reports in the terminal. Do not interact with the main Magic2 window, as who knows what happens then?\n\nThere is a very much non-zero risk of crashing. You may loose your work (so save it)."):
        # If the above checks are passed, perform the triangulation and let
        # set_mode render it
        if env is None:
            env = options.mode.split("_")[0]
        m2triangulate.triangulate_debug(options.objects[env]['canvas'])
        options.mode = env + "_map"
        set_mode(options)


# This function subtracts the interpolated images for plasma and the background
# after checking they exist and showing the appropriate alert if they don't
def subtract(options):
    if options.objects['background']['canvas'] is None:
        mb.showinfo("No background loaded", "You need to load, label, and interpolate a background interferogram file first in order to perform the subtraction.")
    elif not options.objects['background']['canvas'].interpolation_done:
        mb.showinfo("No background interpolation", "You need to perform an interpolation of the background fringes before the subtraction.")
    elif options.objects['plasma']['canvas'] is None:
        mb.showinfo("No background loaded", "You need to load, label, and interpolate a plasma interferogram file first in order to perform the subtraction.")
    elif not options.objects['plasma']['canvas'].interpolation_done:
        mb.showinfo("No background interpolation", "You need to perform an interpolation of the plasma fringes before the subtraction.")
    else:
        # Subtract the interferograms, masking them with the user-defined mask,
        # as well as the regions that couldn't be interpolated for both
        # background and plasma images
        options.subtracted = sp.ma.masked_where(
            sp.logical_or(sp.logical_or(
                options.objects['plasma']['canvas'].mask == False,
                options.objects['plasma']['canvas'].interpolated == -1024.0),
                options.objects['background']['canvas'].interpolated == -1024.0
            ),
            options.objects['background']['canvas'].interpolated
            - options.objects['plasma']['canvas'].interpolated
        )
        # Let set_mode do the rendering
        options.mode = "subtracted_graph"
        set_mode(options)
        return True


class PlasmaDialog(m2dialog.Dialog):
    def __init__(self, parent, options, title=None):
        self.options = options
        m2dialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        master.grid_rowconfigure((0,1,2), pad=5)
        # Resolution
        ttk.Label(master, text="Resolution:").grid(row=0, sticky=Tk.E)
        self.e_resolution = ttk.Entry(master)
        if self.options.resolution is not None:
            self.e_resolution.insert(0, self.options.resolution)
        self.e_resolution.grid(row=0, column=1)
        ttk.Label(master, text="pixels per mm").grid(row=0, column=2, sticky=Tk.W)
        # Depth
        ttk.Label(master, text="Depth of the object:").grid(row=1, sticky=Tk.E)
        self.e_depth = ttk.Entry(master)
        if self.options.depth is not None:
            self.e_depth.insert(0, self.options.depth)
        self.e_depth.grid(row=1, column=1)
        ttk.Label(master, text="mm").grid(row=1, column=2, sticky=Tk.W)
        # Wavelength
        ttk.Label(master, text="Wavelength:").grid(row=2, sticky=Tk.E)
        self.e_wavelength = ttk.Entry(master)
        if self.options.wavelength is not None:
            self.e_wavelength.insert(0, self.options.wavelength)
        self.e_wavelength.grid(row=2, column=1)
        ttk.Label(master, text="nm").grid(row=2, column=2, sticky=Tk.W)
        # Double fringes
        self.double_var = Tk.BooleanVar()
        if self.options.double is not None:
            self.double_var.set(self.options.double)
        self.cb = ttk.Checkbutton(master, text="Double", variable=self.double_var)
        self.cb.grid(row=3, columnspan=3)
        # Return the default input box
        return self.e_resolution

    def validate(self):
        try:
            float(self.e_resolution.get())
            float(self.e_depth.get())
            float(self.e_wavelength.get())
            return 1
        except ValueError:
            mb.showerror("Error", "All values need to be floats or integers!")
            return 0

    def apply(self):
        self.options.resolution = float(self.e_resolution.get())
        self.options.depth = float(self.e_depth.get())
        self.options.wavelength = float(self.e_wavelength.get())
        self.options.double = self.double_var.get()
        self.result = True


def shot_options(options):
    dialog = PlasmaDialog(options.root, options, title="Shot details")
    return dialog.result is not None


def plasma_density(options):
    if options.subtracted is None and subtract(options) is None:
        return False
    if (
        (options.resolution is not None and options.depth is not None
         and options.wavelength is not None and options.double is not None)
        or shot_options(options)
    ):
        c = 3e8
        e = 1.602e-19
        me = 9.109e-31
        e0 = 8.854e-12
        d = options.depth * 1e-3
        wavelength = options.wavelength * 1e-9
        if options.double:
            multiplier = 0.5
        else:
            multiplier = 1
        options.density = (multiplier * options.subtracted * 8
                           * (sp.pi * c / e)**2 * me * e0 / d / wavelength)
        options.mode = "density_graph"
        set_mode(options)


def cosine(options):
    if options.mode.split("_")[1] == 'map':
        options.ax.imshow(sp.cos(options.imshow.get_array()*2*sp.pi), cmap="Greys")
        # Refresh the graph's canvas
        options.fig.canvas.draw()
        # Set the radio buttons to the correct position
        options.show_var.set("cosine_graph")
        options.mode = "cosine_graph"
    else:
        mb.showinfo("Open a map", "Taking the cosine is possible only for interpolated phase maps.")
