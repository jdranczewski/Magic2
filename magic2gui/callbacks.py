import tkinter.filedialog as fd
import tkinter.messagebox as mb
import scipy as sp
import magic2.graphics as m2graphics
import magic2.fringes as m2fringes
import magic2.labelling as m2labelling
import magic2.triangulate as m2triangulate


def open_image(options, env):
    if options.objects[env]['canvas'] is not None and not mb.askokcancel(
        "Overwrite?", "There is a " + env
        + "file open already. Opening a new one will "
        + "overwrite all changes made to it!"
    ):
        pass
    else:
        filename = fd.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")])
        if filename is not None:
            options.status.set("Reading the file", 0)
            if options.objects[env]['canvas'] is not None:
                del options.objects[env]['canvas']
                del options.objects[env]['fringes']
            canvas = options.objects[env]['canvas'] = m2graphics.Canvas(filename)
            options.status.set("Looking for fringes", 33)
            fringes = options.objects[env]['fringes'] = m2fringes.Fringes()
            m2fringes.read_fringes(fringes, canvas)
            options.status.set("Rendering fringes", 66)
            m2graphics.render_fringes(fringes, canvas, width=3)
            options.ax.clear()
            if options.labeller is not None:
                m2labelling.stop_labelling(options.fig, options.labeller)
            canvas.imshow = options.ax.imshow(
                sp.ma.masked_where(canvas.fringe_phases_visual == -1024,
                                   canvas.fringe_phases_visual),
                cmap=m2graphics.cmap
            )
            canvas.imshow.figure.canvas.draw()
            options.labeller = m2labelling.label(fringes, canvas,
                                                 options.fig, options.ax)
            options.current = env
            options.fringes_or_map = 'fringes'
            options.show.set(env+"_fringes")
            options.status.set("Done", 100)


def show_image(options):
    key = options.show.get().split("_")
    if options.objects[key[0]]['canvas'] is None:
        if options.current is not None:
            options.show.set(options.current + "_" + options.fringes_or_map)
        else:
            options.show.set("")
        open_image(options, key[0])
    else:
        canvas = options.objects[key[0]]['canvas']
        fringes = options.objects[key[0]]['fringes']
        if key[1] == "fringes":
            options.current = key[0]
            options.fringes_or_map = key[1]
            options.ax.clear()
            if options.labeller is not None:
                m2labelling.stop_labelling(options.fig, options.labeller)
            canvas.imshow = options.ax.imshow(
                sp.ma.masked_where(canvas.fringe_phases_visual == -1024,
                                   canvas.fringe_phases_visual),
                cmap=m2graphics.cmap
            )
            canvas.imshow.set_clim(0, fringes.max)
            options.labeller = m2labelling.label(fringes, canvas,
                                                 options.fig, options.ax)
        elif canvas.interpolation_done:
            options.current = key[0]
            options.fringes_or_map = key[1]
            options.ax.clear()
            if options.labeller is not None:
                m2labelling.stop_labelling(options.fig, options.labeller)
            canvas.imshow = options.ax.imshow(
                sp.ma.masked_where(sp.logical_or(canvas.mask == False, canvas.interpolated == -1024.0),
                                   canvas.interpolated),
                cmap=m2graphics.cmap
            )
        elif mb.askyesno(
            "Interpolate?", "The interferogram for " + key[0]
            + " has not been interpolated yet. Would you like to do that now?"
        ):
            options.ax.clear()
            if options.labeller is not None:
                m2labelling.stop_labelling(options.fig, options.labeller)
            m2triangulate.triangulate(options.objects[key[0]]['canvas'],
                                      options.ax, options.status)
        elif options.current is not None:
            options.show.set(options.current + "_fringes")
        else:
            options.show.set("")
        canvas.imshow.figure.canvas.draw()
    options.mframe.canvas._tkcanvas.focus_set()


def interpolate(options):
    if options.current is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    else:
        m2labelling.stop_labelling(options.fig, options.labeller)
        m2triangulate.triangulate(options.objects[options.current]['canvas'],
                                  options.ax, options.status)
        options.fringes_or_map = 'map'
        options.show.set(options.current + "_map")


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
        options.subtract = sp.ma.masked_where(
            sp.logical_or(sp.logical_or(
                options.objects['plasma']['canvas'].mask == False,
                options.objects['plasma']['canvas'].interpolated == -1024.0),
                options.objects['background']['canvas'].interpolated == -1024.0
            ),
            options.objects['background']['canvas'].interpolated
            - options.objects['plasma']['canvas'].interpolated
        )
        options.ax.clear()
        if options.labeller is not None:
            m2labelling.stop_labelling(options.fig, options.labeller)
        imshow = options.ax.imshow(options.subtract, cmap=m2graphics.cmap)
        imshow.figure.canvas.draw()
