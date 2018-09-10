import tkinter.filedialog as fd
import tkinter.messagebox as mb
import tkinter as Tk
import tkinter.ttk as ttk
import scipy as sp
from copy import copy
import pickle
import gzip
import os
from matplotlib.pyplot import cm
import matplotlib.ticker as ticker

import magic2gui.dialog as m2dialog
import magic2gui.lineouts as m2lineouts
import magic2.graphics as m2graphics
import magic2.fringes as m2fringes
import magic2.labelling as m2labelling
import magic2.triangulate as m2triangulate


# Open and image for either the background or plasma fringes (determined
# by the env variable)
def open_image(options, env):
    if options.objects[env]['canvas'] is not None and not mb.askokcancel(
        "Overwrite?", "There is a " + env
        + "file open already. Opening a new one will "
        + "overwrite all changes made to it!"
    ):
        pass
    else:
        # Display a window for chooisng the file
        filename = fd.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")],
                                  title="Open "+env+" interferogram")
        if filename is not None:
            options.status.set("Reading the file", 0)
            if not options.ncmanual:
                # Save the name (except for the last word) as a template which will
                # be used when saving files
                options.namecore = os.path.basename(filename.name).rsplit(" ", 1)[0]
                if len(options.namecore.split(".")) > 1:
                    options.namecore = options.namecore.split(".")[0]
                options.status.set_name_label(options.namecore)
            # Delete the old objects if we are overwriting
            if options.objects[env]['canvas'] is not None:
                del options.objects[env]['canvas']
                del options.objects[env]['fringes']
                del options.subtracted
                options.subtracted = None
            # Create a canvas object
            canvas = options.objects[env]['canvas'] = m2graphics.Canvas(filename)
            if canvas.error:
                mb.showerror("File not opened", "There was an error while opening the image. Are you sure it's a .png?")
                options.objects[env]['canvas'] = None
                return False
            options.status.set("Looking for fringes", 33)
            # Extract fringe information from the file
            fringes = options.objects[env]['fringes'] = m2fringes.Fringes()
            m2fringes.read_fringes(fringes, canvas)
            options.status.set("Rendering fringes", 66)
            # Render the fringes onto the canvas
            m2graphics.render_fringes(fringes, canvas, width=options.width_var.get())
            # Reset the image limits
            options.conserve_limits = False
            # Set the mode (the set_mode function handles rendering)
            options.mode = env + "_fringes"
            set_mode(options)
            # Make the software go over the subtraction and plasma density
            # calculation again, as the data has changed
            options.subtracted = None
            options.density = None
            options.offset = 0
            options.status.set("Done", 100)


# Save the minimum of the data necessary to reconstruct the labelling.
# We are not saving all the data, not even the interpolations, as they
# greatly increase the file size required (pictures are big). What we do
# save are the boolean array representing fringes and the user-defined mask,
# and a list of all the assigned phases. As the fringe-reading process is
# completely deterministic, the labelling will be assigned in the correct order
def m_save(options):
    filename = fd.asksaveasfilename(filetypes=[("Magic2 file", "*.m2")],
                                    defaultextension=".m2",
                                    initialfile=options.namecore)
    if filename != '':
        options.status.set("Exporting", 0)
        dump = []
        try:
            dump.append(options.objects['background']['canvas'].fringes_image)
            dump.append(options.objects['background']['canvas'].mask)
            dump.append([fringe.phase for fringe in options.objects['background']['fringes'].list])
        except AttributeError:
            dump = [None, None, None]
        try:
            dump.append(options.objects['plasma']['canvas'].fringes_image)
            dump.append(options.objects['plasma']['canvas'].mask)
            dump.append([fringe.phase for fringe in options.objects['plasma']['fringes'].list])
        except AttributeError:
            dump = dump[:3]
            dump.append(None)
            dump.append(None)
            dump.append(None)
        dump.append(options.offset)
        dump.append(options.namecore)
        dump.append(options.resolution)
        dump.append(options.depth)
        dump.append(options.wavelength)
        dump.append(options.double)
        dump.append(options.centre)
        # We use gzip to make the file smaller. Normal pickling produced files
        # that were around 30MB, while the compressed version of the same data
        # is 188KB
        with gzip.open(filename, 'wb') as f:
            pickle.dump(dump, f)
        options.status.set("Done", 100)


# This function reads data seaved with m_save
def m_open(options, interpolate = None):
    if (options.objects['background']['canvas'] is not None or options.objects['plasma']['canvas'] is not None) and not mb.askokcancel("Discard data?", "Discard current data? Opening an .m2 file will overwrite any data you are currently working on."):
        return False
    filename = fd.askopenfile(filetypes=[("Magic2 files", "*.m2")])
    if filename is not None:
        # We need to use gzip to decompress the .m2 file
        with gzip.open(filename.name, 'rb') as f:
            options.status.set("Loading file", 0)
            dump = pickle.load(f)
            for env, i in (('background', 0), ('plasma', 3)):
                if dump[i] is not None:
                    # Delete the old data
                    if options.objects[env]['canvas'] is not None:
                        del options.objects[env]['canvas']
                        del options.objects[env]['fringes']
                        del options.subtracted
                    options.status.set("Reading "+env+" canvas", i%2*45 + 10)
                    # Create a new Canvas object
                    canvas = options.objects[env]['canvas'] = m2graphics.Canvas('dump', fi=dump[i], m=dump[i+1])
                    options.status.set("Finding "+env+" fringes", i%2*45 + 20)
                    # Create a new fringes object
                    fringes = options.objects[env]['fringes'] = m2fringes.Fringes()
                    # Set the max and min for the colormap to have a correct scale
                    fringes.min = sp.amin([phase for phase in dump[i+2] if phase != -2048.0])
                    fringes.max = sp.amax([phase for phase in dump[i+2] if phase != -2048.0])
                    # Read the fringes, assigning phases as we go
                    m2fringes.read_fringes(fringes, canvas, phases=dump[i+2])
                    options.status.set("Rendering "+env+" fringes", i%2*45 + 35)
                    # Render the fringes
                    m2graphics.render_fringes(fringes, canvas, width=options.width_var.get())
                    # Indicate that the subtracted and density maps need to be
                    # recalculated
                    options.subtracted = None
                    options.density = None
            # Set the shot options
            options.offset = dump[6]
            options.namecore = dump[7]
            options.status.set_name_label(options.namecore)
            options.resolution = dump[8]
            options.depth = dump[9]
            options.wavelength = dump[10]
            options.double = dump[11]
            # For saved variables introduced in v1.02
            try:
                options.centre = dump[12]
            except IndexError:
                # The centre option is set to a default of [0, 0] when creating
                # the Options object.
                pass
            options.status.set("Done", 100)
            # If data is available for either background or plasma fringes,
            # display them
            if dump[0] is not None:
                options.conserve_limits = False
                options.mode = "background_fringes"
                set_mode(options)
            elif dump[3] is not None:
                options.conserve_limits = False
                options.mode = "plasma_fringes"
                set_mode(options)
            # Allow for automatic interpolation of the just-loaded
            # interfererograms
            if interpolate == "fast":
                if dump[0] is not None:
                    interpolate_fast(options, env='background')
                if dump[3] is not None:
                    interpolate_fast(options, env='plasma')
            elif interpolate == "exact":
                if dump[0] is not None:
                    interpolate_exact(options, env='background')
                if dump[3] is not None:
                    interpolate_exact(options, env='plasma')


# This dialog is used for exporting the graph as an image.
# It allows the user to choose a resolution
class NameDialog(m2dialog.Dialog):
    def __init__(self, parent, options, title=None):
        # We need to save the options, which would not be accepted as an
        # argument by the original Dialog class, so we override __init__
        self.options = options
        m2dialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        # Create a simple body
        ttk.Label(master, text="Project name:").grid(row=0)
        self.e = ttk.Entry(master)
        if self.options.namecore is not None:
            self.e.insert(0, self.options.namecore)
        self.e.grid(row=0, column=1)
        return self.e

    def apply(self):
        # Save the value from the text field as .result
        self.result = self.e.get()


# This function sets the project's name
def set_namecore(options):
    dialog = NameDialog(options.root, options, title="Set name")
    if dialog.result is not None:
        options.namecore = dialog.result
        options.ncmanual = True
        options.status.set_name_label(options.namecore)


# Export the data from the current view
def export(options):
    if options.mode is not None:
        filename = fd.asksaveasfilename(filetypes=[(".csv file", "*.csv"),
                                                   ("All files", "*")],
                                        defaultextension=".csv",
                                        initialfile=options.namecore)
        if filename != '':
            options.status.set("Exporting", 0)
            # The mask is filled with -1024 to make the masking uniform
            if options.mode.split("_")[1] == 'fringes':
                fringe_phases = options.objects[options.mode.split("_")[0]]['canvas'].fringe_phases.astype(float)
                sp.savetxt(filename, sp.ma.filled(
                    sp.ma.masked_where(fringe_phases==-1024.0, fringe_phases),
                    fill_value=sp.nan), delimiter=",", fmt="%.0f")
            else:
                sp.savetxt(filename, sp.ma.filled(options.imshow.get_array(),fill_value=sp.nan), delimiter=",")
            options.status.set("Done", 100)
    else:
        mb.showinfo("No mode chosen", "Please choose one of the display modes from the menu on the right!")


# This dialog is used for exporting the graph as an image.
# It allows the user to choose a resolution
class DpiDialog(m2dialog.Dialog):
    def body(self, master):
        # Create a simple body
        ttk.Label(master, text="DPI:").grid(row=0)
        self.e = ttk.Entry(master)
        self.e.insert(0, 300)
        self.e.grid(row=0, column=1)
        return self.e

    def validate(self):
        # Check if the value entered is an integer
        try:
            int(self.e.get())
            return 1
        except ValueError:
            mb.showerror("Error", "The value needs to be an integer!")
            return 0

    def apply(self):
        # Save the value from the text field as .result
        self.result = int(self.e.get())


# This function exports the current graph as an image
def export_image(options):
    dialog = DpiDialog(options.root, title="Choose quality")
    if dialog.result is not None:
        # Ask for a file name
        filename = fd.asksaveasfilename(filetypes=[("PNG files", "*.png;*.PNG"),
                                                   ("All files", "*")],
                                        defaultextension=".png",
                                        initialfile=options.namecore)
        if filename != '':
            # Save the graph, using the dpi obtained with the dialog
            options.fig.savefig(filename, dpi=dialog.result)


# This dialog is used by the function that sets the colormap
class CmapDialog(m2dialog.Dialog):
    def __init__(self, parent, options, title=None):
        # We need to save the options, which would not be accepted as an
        # argument by the original Dialog class, so we override __init__
        self.options = options
        m2dialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        ttk.Label(master, text="Colormap:").grid(row=0)
        self.var = Tk.StringVar()
        # This is a list of all reasonable colourmaps in matplotlib,
        # reasonable meaning that they're rather smooth and not the
        # flag of France
        choice = ('## perceptually uniform ##', 'plasma', 'viridis', 'inferno',
                  'magma', '## the classic ##', 'jet', '## sequnetial ##',
                  'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                  'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                  'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
                  'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
                  'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
                  'hot', 'afmhot', 'gist_heat', 'copper', '## misc ##', 'ocean',
                  'gist_earth', 'terrain', 'gist_stern', 'gnuplot',
                  'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'hsv',
                  'gist_rainbow', 'rainbow', 'nipy_spectral', 'gist_ncar')
        # The star (*) unpacks the above tuple, as ttk.OptionMenu takes options
        # as just a lot of arguments
        self.e = ttk.OptionMenu(master, self.var, self.options.cmap.name, *choice)
        self.e.grid(row=0, column=1)
        return self.e

    def validate(self):
        if self.var.get()[:2] != "##":
            return 1
        else:
            # This is necessary as not all things on the list are colormaps
            mb.showerror("Error", "Choose a valid colormap.")
            return 0

    def apply(self):
        self.result = self.var.get()


# This function sets a chosen colormap
def set_colormap(options):
    dialog = CmapDialog(options.root, options)
    if dialog.result is not None:
        options.cmap = copy(cm.get_cmap(dialog.result))
        # White is for masking
        options.cmap.set_bad('white', 1.0)
        # Black is for unlabelled fringes
        options.cmap.set_under('black', 1.0)
        # Refresh the graph if needed
        if options.mode is not None:
            set_mode(options)


class FastExactDialog(m2dialog.Dialog):
    def body(self, master):
        labelframe = Tk.Frame(master, bg='#fff')
        labelframe.pack(fill=Tk.BOTH, expand=1)
        label = Tk.Label(labelframe, text="Choose an interpolation mode. The fast one is fast, but less exact. The slow one removes flat triangles from the triangulation that is used when interpolating.", background='#fff', wraplength=350, padx=15, pady=15, justify=Tk.LEFT, anchor=Tk.W)
        label.pack(fill=Tk.BOTH, expand=1)

    # Create the buttons
    def buttonbox(self):
        box = Tk.Frame(self)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=Tk.RIGHT, padx=5, pady=5)
        w = ttk.Button(box, text="Slow and exact", width=15, command=self.slow)
        w.pack(side=Tk.RIGHT, padx=5, pady=5)
        w = ttk.Button(box, text="Fast", width=10, command=self.fast,
                       default=Tk.ACTIVE)
        w.pack(side=Tk.RIGHT, padx=5, pady=5)
        self.bind("<Return>", self.fast)
        self.bind("<Escape>", self.cancel)
        box.pack(fill=Tk.BOTH, padx=10, pady=5)

    def fast(self, *args):
        self.result = "Fast"
        self.ok()

    def slow(self):
        self.result = "Slow"
        self.ok()


# Handle the user choosing one of the radio buttons
def show_radio(options):
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
                dialog = FastExactDialog(options.root, title="Fast or exact?", pad=False)
                if dialog.result == "Slow":
                    interpolate_exact(options, key[0])
                elif dialog.result == "Fast":
                    interpolate_fast(options, key[0])

    # If the user wants the subtracted map, show it or calculate it and show it
    # (the calculation is a quick process, so it doesn't make sense to ask
    # the user for permission)
    elif key[0] == 'subtracted':
        if options.subtracted is None:
            subtract(options)
        else:
            options.mode = "_".join(key)
            set_mode(options)
    # Similarly for the density map
    elif key[0] == 'density':
        if options.density is None:
            plasma_density(options)
        else:
            options.mode = "_".join(key)
            set_mode(options)
    # Give the focus back to the graph
    options.mframe.canvas._tkcanvas.focus_set()


# Allow for quick recomputing of whatever is being right-clicked on
# the radio buttons on the right
def recompute(event, options):
    key = event.widget['value'].split("_")
    if key[1] == 'fringes':
        phases = [fringe.phase for fringe in options.objects[key[0]]['fringes'].list]
        try:
            options.objects[key[0]]['fringes'].min = sp.amin([phase for phase in phases if phase != -2048.0])
            options.objects[key[0]]['fringes'].max = sp.amax([phase for phase in phases if phase != -2048.0])
            set_mode(options)
        except ValueError:
            pass
    if key[1] == 'map':
        options.show_var.set(event.widget['value'])
        if options.objects[key[0]]['canvas'] is not None:
            options.objects[key[0]]['canvas'].interpolation_done = False
        # Let the show_radio function handle all the logic and dialogs
        # that are needed here
        show_radio(options)
    elif key[0] == 'subtracted':
        subtract(options)
    elif key[0] == 'density':
        plasma_density(options)


# Render the correct image on the graph's canvas
# Also used for refreshing
def set_mode(options):
    key = options.mode.split("_")
    # This allows one to stop the conserve_limits variable from switching
    # back to True after the function executes
    stop_reverting = False
    if options.conserve_limits:
        # Get the current display limits
        ylim = options.ax.get_ylim()
        xlim = options.ax.get_xlim()
    if options.lineout_meta is not None:
        m2lineouts.stop_lineout(options)
    # Clear the axes and all labellers/event handlers attached to them
    # (if they exist)
    options.ax.clear()
    if options.labeller is not None:
        m2labelling.stop_labelling(options.fig, options.labeller)
        options.labeller = None
    if options.cbar is not None:
        # If there exists a colorbar, clean it and hide it
        options.mframe.cax.clear()
        options.mframe.cax.axis('off')
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
                                             options=options, imshow=options.imshow)
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
        options.imshow = options.ax.imshow(options.subtracted-options.offset, cmap=options.cmap)
        # Add a colorbar using its own subplot
        options.cbar = options.fig.colorbar(options.imshow, cax=options.mframe.cax)
        # Unhide the colorbar's subplot
        options.mframe.cax.axis('on')
        # Add a label. Rotation is os that it's easier to read, labelpad
        # stops it from touching the colorbar's ticks' labels
        options.cbar.ax.set_ylabel('Fringe shift', rotation=270, labelpad=20)
    elif key[0] == 'density':
        y_size, x_size = options.density.shape
        extent = sp.array([0-options.centre[1],x_size-options.centre[1],y_size-options.centre[0],0-options.centre[0]])/options.resolution
        # Don't conserve limits (we're changing the range here)
        options.conserve_limits = False
        # This means that next time we switch mode, the limits will be reset:
        stop_reverting = True
        options.imshow = options.ax.imshow(options.density, cmap=options.cmap, extent=extent)
        # Add x and y axis labels
        options.ax.set_xlabel("Distance / $mm$")
        options.ax.set_ylabel("Distance / $mm$")
        options.cbar = options.fig.colorbar(options.imshow, cax=options.mframe.cax)
        options.mframe.cax.axis('on')
        options.cbar.ax.set_ylabel('Electron density / $cm^{-3}$', rotation=270, labelpad=20)
    if options.conserve_limits:
        # revert the graph to the old display limits
        options.ax.set_xlim(xlim)
        options.ax.set_ylim(ylim)
    elif not stop_reverting:
        # Revert to the original setting
        options.conserve_limits = True
    # Update all the active lineouts
    for lineout in options.lineouts:
        lineout.update()
    # Refresh the graph's canvas
    options.fig.canvas.draw()
    # Set the radio buttons to the correct position
    options.show_var.set(options.mode)
    # Give the focus back to the graph
    options.mframe.canvas._tkcanvas.focus_set()


# Decrease the width of the rendered fringes
def lower_width(options):
    if options.mode is None or options.mode.split("_")[1] != "fringes":
        mb.showinfo("Not in fringe display mode", "You need to be in a fringe display mode to change the width setting.")
    else:
        # Check if the decreasing is possible
        if options.width_var.get() > 0:
            options.width_var.set(options.width_var.get() - 1)
            if options.objects['background']['canvas'] is not None:
                # We need to clear the canvas, as the new rendering is always
                # on top. This saves time when only some fringe were relabelled
                # by not rendering it all, but here it would mean that the
                # smaller fringes appear inside the larger ones
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
            # We don't need to clear the canvas here, the new drawings are
            # wider and will therefore cover the old ones
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
        # If the above checks are passed, perform the triangulation and
        # interpolation, and let set_mode render it
        if env is None:
            env = options.mode.split("_")[0]
        tri = m2triangulate.triangulate(options.objects[env]['canvas'],
                                        options.ax, options.status)
        if tri is None:
            mb.showerror("Triangulation failed", "No points detected, so the triangulation failed. Have you labelled the fringes?")
        else:
            options.mode = env + "_map"
            set_mode(options)


# This performs a fast version of the interpolation, which does not fix
# flat triangles
def interpolate_fast(options, env=None):
    if options.mode is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    elif options.mode.split("_")[0] != 'plasma' and options.mode.split("_")[0] != 'background':
        mb.showinfo("No mode chosen", "Please choose either the background or plasma display mode from the menu on the right!")
    else:
        # If the above checks are passed, perform the triangulation and
        # interpolation, and let set_mode render it
        if env is None:
            env = options.mode.split("_")[0]
        tri = m2triangulate.fast_tri(options.objects[env]['canvas'],
                                     options.ax, options.status)
        if tri is None:
            mb.showerror("Triangulation failed", "No points detected, so the triangulation failed. Have you labelled the fringes?")
        else:
            options.mode = env + "_map"
            set_mode(options)


# This performs the interpolation in debug mode, meaning feedback is in
# instead of the status bar, and output of every step is displayed in
# a separate window
def interpolate_debug(options, env=None):
    if options.mode is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    elif options.mode.split("_")[0] != 'plasma' and options.mode.split("_")[0] != 'background':
        mb.showinfo("No mode chosen", "Please choose either the background or plasma display mode from the menu on the right!")
    elif mb.askokcancel("Debug triangulation", "You are about to perform a debug mode interpolation. This shows the output of every step in a separate graph window. Close that window to proceed to the next step. Flat triangles are usually highlighted green. Look for error messages and progress reports in the terminal. Do not interact with the main Magic2 window, as who knows what happens then?\n\nThere is a very much non-zero risk of crashing. You may loose your work (so save it)."):
        # The above confirmation dialog is unwieldy, but necessary to explain
        # the risks and advantages to the user
        if env is None:
            env = options.mode.split("_")[0]
        m2triangulate.triangulate_debug(options.objects[env]['canvas'], options)
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
        # try:
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
        # except ValueError:
        #     mb.showinfo("Wrong shape", "The shapes of the background and plasma images are different ({} and {}). They need to be the same for the subtraction to be performed!".format(options.objects['background']['canvas'].interpolated.shape, options.objects['plasma']['canvas'].interpolated.shape))


# This dialog allows the user to set the shift that should be normalised
# to be zero.
class ZeroDialog(m2dialog.Dialog):
    def __init__(self, parent, options, title=None):
        # We need to save the options, which would not be accepted as an
        # argument by the original Dialog class, so we override __init__
        self.options = options
        m2dialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        # Create a simple body
        ttk.Label(master, text="Set the value of fringe shift that should be normalised to be zero.\n\n"
                               "If you choose the automatic (Auto) option, Magic2 will take the lowest\n"
                               "fringe shift and set that as the zero point.\n",
                               anchor=Tk.CENTER).grid(row=0, columnspan=2)
        ttk.Label(master, text="Zero point:  ").grid(row=1, sticky=Tk.E)
        self.e = Tk.Spinbox(master, from_=-1024.0, to=1024.0, increment=1.0)
        self.e.delete(0, Tk.END)
        self.e.insert(Tk.END, self.options.offset)
        self.e.grid(row=1, column=1, sticky=Tk.W)
        return self.e

    # Create the buttons
    def buttonbox(self):
        box = Tk.Frame(self)
        w = ttk.Button(box, text="OK", width=10, command=self.ok,
                       default=Tk.ACTIVE)
        w.pack(side=Tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Auto", width=10, command=self.auto)
        w.pack(side=Tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=Tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def auto(self):
        self.result = "auto"
        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def validate(self):
        try:
            # All the inputs should be floats or integers
            float(self.e.get())
            return 1
        except ValueError:
            mb.showerror("Error", "The zero value needs to be a float or an integer!")
            return 0

    def apply(self):
        # Save the value from the text field as .result
        self.result = float(self.e.get())


# The main function for zero-setting
def set_zero(options):
    # Check if mode is correct
    if options.mode == "subtracted_graph":
        dialog = ZeroDialog(options.root, options, title="Choose zero point")
        if dialog.result == "auto":
            options.offset = sp.amin(options.subtracted)
        elif dialog.result is not None:
            options.offset = dialog.result
        set_mode(options)
    else:
        mb.showinfo("Not in subtracted mode", "You need to be in the subtracted map mode to set the zero shift point.")


# This function inverts the currently displayed view
def invert(options):
    if options.mode is not None:
        key = options.mode.split("_")
        if key[1] == 'map':
            interpolated = options.objects[key[0]]['canvas'].interpolated
            # Using a mask ensures we do not touch the -1024 pixels
            # (they indicate that no data is available)
            mask = interpolated != -1024.0
            interpolated[mask] = -interpolated[mask]
            set_mode(options)
            # This return is a convenient way of escaping the function before
            # The error message is shown
            return True
        elif key[0] == 'subtracted':
            options.subtracted = -options.subtracted
            set_mode(options)
            return True
        elif key[0] == 'density':
            options.density = -options.density
            set_mode(options)
            return True
    mb.showerror("Not available in this mode", "To invert data you have to be viewing an interpolation, subtraction or a plasma density map.")


# This dialog is used to obtain/display the shot details
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
            # All the inputs should be floats or integers
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


# This function shows the above dialog
def shot_options(options):
    dialog = PlasmaDialog(options.root, options, title="Shot details")
    return dialog.result is not None


# This function calculates the plasma density map
def plasma_density(options):
    if options.subtracted is None and subtract(options) is None:
        return False
    # This checks whether the options are all set - if not, it asks for them
    if (
        (options.resolution is not None and options.depth is not None
         and options.wavelength is not None and options.double is not None)
        or shot_options(options)
    ):
        # Speed of light
        c = 3e8
        # Electron charge
        e = 1.602e-19
        # Electron mass
        me = 9.109e-31
        # Permittivity of free space
        e0 = 8.854e-12
        # Sample depth in meters
        d = options.depth * 1e-3
        # Wavelength in meters
        wavelength = options.wavelength * 1e-9
        # If the double option was chosen, one traced fringe corresponds
        # to half a fringe shift
        if options.double:
            multiplier = 0.5
        else:
            multiplier = 1
        # Calculate the density map
        options.density = (multiplier * (options.subtracted-options.offset) * 8
                           * (sp.pi * c / e)**2 * me * e0 / d / wavelength)
        # Convert to centimetres cubed
        options.density /= 1e6
        # Let set_mode render the map
        options.mode = "density_graph"
        set_mode(options)


# Event handler for setting the centre of the density map
def set_centre_onclick(event, options, binds):
    options.centre = [event.ydata*options.resolution, event.xdata*options.resolution]
    # Unbind all the event handlers
    for bind in binds:
        options.fig.canvas.mpl_disconnect(bind)
    # Allow the graph to resize after the centre is set
    options.conserve_limits = False
    set_mode(options)
    options.mframe.config(cursor="")


# Event handler for cancelling the process of setting the centre
# of the density map
def set_centre_onpress(event, options, binds):
    if event.key == "escape":
        for bind in binds:
            options.fig.canvas.mpl_disconnect(bind)
        options.mframe.config(cursor="")


# Set centre of the plasma density map
def set_centre(options):
    if options.mode == "density_graph":
        ans = mb.askyesnocancel("Set centre?", "Press 'Yes' and then click anywhere on the graph to set the centre of the density map. Use the escape key to cancel.\n\n"
                                "Press 'No' to reset the centre to [0, 0].")
        if ans:
            options.mframe.config(cursor="crosshair")
            binds = [None, None]
            binds[0] = options.fig.canvas.mpl_connect('button_press_event',
                lambda event: set_centre_onclick(event, options, binds))
            binds[1] = options.fig.canvas.mpl_connect('key_press_event',
                lambda event: set_centre_onpress(event, options, binds))
        elif ans is not None:
            options.centre = [0, 0]
            set_mode(options)
    else:
        mb.showinfo("Not in plasma density mode", "You need to be in the plasma density map mode to set the centre of that map.")


# Take the cosine of a phase map. It should look very similar to the picture
# from which the fringe lines were traced
def cosine(options):
    if options.mode.split("_")[1] == 'map':
        if options.double is True:
            multiplier = 1
        else:
            multiplier = 2
        # This mode is a spetial little snowflake, in that it doesn't have
        # a radio button or a set_mode if clause. We handle its rendering
        # ourselves here:
        # Clear the canvas
        options.ax.clear()
        # Draw the cosine
        options.imshow = options.ax.imshow(sp.cos(options.imshow.get_array()*multiplier*sp.pi), cmap="Greys")
        # Set the mode variable
        mode = options.mode.split("_")[0]+"_cosine_graph"
        options.show_var.set(mode)
        options.mode = mode
        # Take care of the lineouts
        if options.lineout_meta is not None:
            m2lineouts.stop_lineout(options)
        for lineout in options.lineouts:
            lineout.update()
        # Draw the canvas
        options.fig.canvas.draw()
    else:
        mb.showinfo("Open a map", "Taking the cosine is possible only for interpolated phase maps.")


def lineout(options):
    if options.mode is not None:
        m2lineouts.create_lineout(options)
    else:
        mb.showinfo("No mode chosen", "Please choose one of the display modes from the menu on the right!")


class AboutDialog(m2dialog.Dialog):
    def body(self, master):
        photo = Tk.PhotoImage(file="logo_s.png")
        logo = Tk.Label(master, image=photo)
        logo.photo = photo
        logo.pack()
        label = Tk.Label(master, text="This software was created by Jakub Dranczewski during a UROP in 2018.\nIt is based on concepts from Magic, which was created by George Swadling.\n\nYou can contact me on jbd17@ic.ac.uk or (as I inevitably loose either the whole email or the 17) jakub.dranczewski@gmail.com\n\nv1.02")
        label.pack()

    def buttonbox(self):
        pass


def about(options):
    AboutDialog(options.root)


def close_window(options):
    if mb.askokcancel("Quit", "Do you actually want to quit?"):
        options.root.destroy()
