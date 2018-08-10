import tkinter.filedialog
import matplotlib.pyplot as plt
import magic2.fringes as m2fringes
import magic2.graphics as m2graphics
import numpy as np


def main():
    filename = tkinter.filedialog.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")])
    print("Reading from", filename.name)
    # A canvas object is created. It handles extracting the fringes and the
    # mas out of the image. It also stores the fringe phases and indices
    # in an array the shape of the initial image for easy referencing
    canvas = m2graphics.Canvas(filename)
    fringes = m2fringes.Fringes()
    # Fringes are read out of the image and stored in Fringe objects
    # fringes.list stores a list of pointers to those obejcts
    m2fringes.read_fringes(fringes, canvas.fringes_image)

    m2graphics.render_fringes(fringes, canvas, width=3)
    plt.imshow(canvas.fringe_phases,  norm=m2graphics.norm, cmap=m2graphics.cmap)
    plt.show()


if __name__ == "__main__":
    main()
