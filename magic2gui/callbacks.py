import tkinter.filedialog
import scipy as sp
import magic2.graphics as m2graphics
import magic2.fringes as m2fringes
import magic2.labelling as m2labelling


def open_background_image(options, imshow):
    filename = tkinter.filedialog.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")])
    if filename is not None:
        canvas = options.objects['background']['canvas'] = m2graphics.Canvas(filename)
        fringes = options.objects['background']['fringes'] = m2fringes.Fringes()
        m2fringes.read_fringes(fringes, canvas)
        m2graphics.render_fringes(fringes, canvas, width=3)
        options.ax.clear()
        canvas.imshow = options.ax.imshow(sp.ma.masked_where(canvas.fringe_phases_visual == -1024, canvas.fringe_phases_visual))
        canvas.imshow.figure.canvas.draw()
        m2labelling.label(fringes, canvas, options.fig, options.ax)
