import tkinter.filedialog
import matplotlib.pyplot as plt
import magic2.fringes as m2fringes
import magic2.graphics as m2graphics
import numpy as np


def main():
    filename = tkinter.filedialog.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")])
    print("Reading from", filename.name)
    # An image is loaded, and only its first colour component is taken
    # out of red, green, blue, alpha. The .png images supplied are greyscale.
    image = plt.imread(filename.name)[:, :, 0]
    fringes_image = image == 0
    fringes = m2fringes.Fringes()
    # Fringes are read out of the image and stored in Fringe objects
    # fringes.list stores a list of pointers to those obejcts
    m2fringes.read_fringes(fringes, fringes_image)
    print(fringes.list)

    canvas = np.zeros_like(fringes_image)
    m2graphics.render_fringes(fringes, canvas)
    plt.imshow(canvas)
    plt.show()


if __name__ == "__main__":
    main()
