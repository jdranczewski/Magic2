# Magic2 (https://github.com/jdranczewski/Magic2)
# Copyright (C) 2018  Jakub Dranczewski, based on work by George Swadling

# This work was carried out during a UROP with the MAGPIE Group,
# Department of Physics, Imperial College London and was supported in part
# by the Engineering and Physical Sciences Research Council (EPSRC) Grant
# No. EP/N013379/1, by the U.S. Department of Energy (DOE) Awards
# No. DE-F03-02NA00057 and No. DE-SC- 0001063

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
