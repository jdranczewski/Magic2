import tkinter.filedialog as fd
import tkinter.messagebox as mb
import scipy as sp
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
            elif mb.askyesno(
                "Interpolate?", "The interferogram for " + key[0]
                + " has not been interpolated yet. Would you like to do that now?"
            ):
                interpolate(options, key[0])
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
    elif key[0] == 'plasma':
        pass


# Render the correct image on the graph's canvas
def set_mode(options):
    key = options.mode.split("_")
    # Clear the axes and all labellers/event handlers attached to them
    # (if they exist)
    options.ax.clear()
    if options.labeller is not None:
        m2labelling.stop_labelling(options.fig, options.labeller)
    if key[1] == 'fringes':
        canvas = options.objects[key[0]]['canvas']
        fringes = options.objects[key[0]]['fringes']
        # The fringes image is masked where there is no data
        options.imshow = canvas.imshow = options.ax.imshow(
            sp.ma.masked_where(canvas.fringe_phases_visual == -1024,
                               canvas.fringe_phases_visual),
            cmap=m2graphics.cmap
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
            cmap=m2graphics.cmap
        )
    elif key[0] == 'subtracted':
        # Show the subtracted image
        # note: this function works on the assumption that the things it is
        # attempting to show have been generated previously. It is the burden
        # of event handlers to check whether this is corrct
        options.imshow = options.ax.imshow(options.subtracted, cmap=m2graphics.cmap)
    elif key[0] == 'plasma':
        pass
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
def interpolate(options, env=None):
    if options.mode is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    elif options.mode.split("_")[0] != 'plasma' and options.mode.split("_")[0] != 'background':
        mb.showinfo("No mode chosen", "Please choose either the background or plasma display mode from the menu on the right!")
    else:
        ans = mb.askyesnocancel("Fast or exact?", "Would you remove flat triangles from the triangulation? This is slower, but more exact..")
        if ans:
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
        elif ans is not None:
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
