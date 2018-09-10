from tkinter import Tk
import tkinter.filedialog
import matplotlib.pyplot as plt
import magic2.fringes as m2fringes
import magic2.graphics as m2graphics
import magic2.labelling as m2labelling
import magic2.triangulate as m2triangulate
import scipy as sp


def main():
    root = Tk()
    filename = tkinter.filedialog.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")])
    root.destroy()
    print("Reading from", filename.name)
    # A canvas object is created. It handles extracting the fringes and the
    # mas out of the image. It also stores the fringe phases and indices
    # in an array the shape of the initial image for easy referencing
    canvas = m2graphics.Canvas(filename)
    fringes = m2fringes.Fringes()
    # Fringes are read out of the image and stored in Fringe objects
    # fringes.list stores a list of pointers to those obejcts
    m2fringes.read_fringes(fringes, canvas)

    m2graphics.render_fringes(fringes, canvas, width=3)
    fig, ax = plt.subplots()
    canvas.imshow = ax.imshow(sp.ma.masked_where(canvas.fringe_phases_visual == -1024, canvas.fringe_phases_visual), cmap=m2graphics.cmap)
    m2labelling.label(fringes, canvas, fig, ax)
    plt.show()

    m2triangulate.triangulate_debug(canvas)


if __name__ == "__main__":
    main()
