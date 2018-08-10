import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from copy import copy


class Canvas():
    def __init__(self, filename):
        # An image is loaded, and only its first colour component is taken
        # out of red, green, blue, alpha.
        # sThe .png images supplied are greyscale.
        image = plt.imread(filename.name)[:, :, 0]
        self.fringes_image = image == 0
        self.mask = np.logical_or(image == 1, self.fringes_image)
        self.fringe_phases_visual = np.zeros_like(self.fringes_image)-1
        self.fringe_phases = np.zeros_like(self.fringes_image)-1
        self.fringe_indices = np.zeros_like(self.fringes_image)-1
        self.imshow = None


# This function can be used to draw the fringes on a given canvas
# at a specified line width. 'fringes' is a Fringes object.
def render_fringes(fringes, canvas, width=1):
    # Hovewer nasty this nested loop looks, it allows us to easily iterate
    # over all points in all fringes. The x range and y range are also
    # executed only once if width is 0
    for fringe in fringes.list:
        for point in fringe.points:
            # This try...excpt saves us from problems with running out
            # of canvas space while alerting us of other valid errors
            # that could occur
            try:
                canvas.fringe_phases[point[0],
                                     point[1]] = fringe.phase
                canvas.fringe_indices[point[0],
                                      point[1]] = fringe.index
            except IndexError:
                pass
            # The width is used only for drawing the visual representation
            # of the fringes
            for x in range(-width+1, width):
                for y in range(-width+1, width):
                    try:
                        canvas.fringe_phases_visual[point[0]+y,
                                                    point[1]+x] = fringe.phase
                    except IndexError:
                        pass


# This function can be used to draw the fringes on a given canvas
# at a specified line width. 'fringes' is a Fringes object.
# It is analogue to 'render_fringes', but it only renders the
# array which is used for displaying the fringes without updating
# the metadata array. Useful for changing width of the rendered fringes
def render_fringes_visual(fringes, canvas, width=1):
    for fringe in fringes.list:
        for point in fringe.points:
            for x in range(-width+1, width):
                for y in range(-width+1, width):
                    try:
                        canvas.fringe_phases_visual[point[0]+y,
                                                    point[1]+x] = fringe.phase
                    except IndexError:
                        pass


# Define a normalization and a colour map that can be used with
# matplotlib's imshow to show phase in a good looking way and on
# a white background.
norm = Normalize(vmin=-0.5, clip=False)
cmap = copy(plt.cm.get_cmap('jet'))
cmap.set_under('white')
