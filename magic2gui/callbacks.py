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
            options.status.set("Done", 100)

def interpolate(options):
    if options.current is None:
        mb.showinfo("No file loaded", "You need to load and label an interferogram file first in order to interpolate the phase!")
    else:
        m2labelling.stop_labelling(options.fig, options.labeller)
        m2triangulate.triangulate(options.objects[options.current]['canvas'], options.ax, options.status)
