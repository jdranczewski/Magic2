import tkinter.filedialog
import matplotlib.pyplot as plt
import magic2.fringes as m2fringes
import numpy as np


def main():
    filename = tkinter.filedialog.askopenfile(filetypes=[("PNG files", "*.png;*.PNG")])
    print(filename.name)
    # An image is loaded, and only its first colour component is taken
    # out of red, green, blue, alpha. The .png images supplied are greyscale.
    image = plt.imread(filename.name)[:, :, 0]
    fringes_image = image == 0
    fringes = m2fringes.Fringes()
    m2fringes.read_fringes(fringes, fringes_image)


if __name__ == "__main__":
    main()
