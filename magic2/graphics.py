import scipy as sp
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from copy import copy


class Canvas():
    def __init__(self, filename, imshow=None):
        # An image is loaded, and only its first colour component is taken
        # out of red, green, blue, alpha.
        # The .png images supplied are greyscale.
        image = plt.imread(filename.name)[:, :, 0]
        # Fringes are black, extract them from the image
        self.fringes_image = image == 0
        # This will store only the labelled fringes, currently empty
        self.fringes_image_clean = sp.zeros_like(self.fringes_image)-0
        # This is the user defined mask, it was grey (so neither black nor
        # white, which is the condition we're using here)
        self.mask = sp.logical_or(image == 1, self.fringes_image)
        # -1024 indicates an area where there is no data
        # Visual stores the fringe phases, but allows for width, making
        # the fringes easier to display
        self.fringe_phases_visual = sp.zeros_like(self.fringes_image)-1024
        # In fringe_phases all the fringes have their initial width
        self.fringe_phases = sp.zeros_like(self.fringes_image)-1024
        # Indexing starts at 0, so -1 is a good choice for 'not an index'
        self.fringe_indices = sp.zeros_like(self.fringes_image)-1
        # x and y are used during interpolation processes to make
        # calculations easier, they store the x and y position of
        # every pixel
        self.x, self.y = sp.meshgrid(sp.arange(0, len(self.fringes_image[0])),
                                     sp.arange(0, len(self.fringes_image)))
        # Interpolated will store the interpolated version of the image
        self.interpolation_done = False
        self.interpolated = sp.zeros_like(self.fringes_image)-1024.0
        # this parameter will store the object returned by matplotlib's
        # imshow function, making it easy to change the data being displayed
        self.imshow = imshow


# This function can be used to draw the fringes on a given canvas
# at a specified line width. 'fringes' is a Fringes object.
def render_fringes(fringes, canvas, width=0, indices=None):
    # Passing indices as an argument allows us to render only
    # the necessary subset of fringes.
    if indices:
        fringe_list = [fringes.list[i] for i in indices]
    else:
        fringe_list = fringes.list
    # Hovewer nasty this nested loop looks, it allows us to easily iterate
    # over all points in all fringes. The x range and y range are also
    # executed only once if width is 0
    for fringe in fringe_list:
        for point in fringe.points:
            # This try...excpt saves us from problems with running out
            # of canvas space while alerting us of other valid errors
            # that could occur
            try:
                canvas.fringe_phases[point[0],
                                     point[1]] = fringe.phase
                canvas.fringe_indices[point[0],
                                      point[1]] = fringe.index
                # fringes_image_clean contains only fringes that
                # have been labelled
                if fringe.phase != -2048:
                    canvas.fringes_image_clean[point[0],
                                               point[1]] = 1
            except IndexError:
                pass
            # The width is used only for drawing the visual representation
            # of the fringes
            try:
                canvas.fringe_phases_visual[point[0]-width:point[0]+width+1,
                                            point[1]-width:point[1]+width+1] = fringe.phase
            except IndexError:
                pass


# Define a normalization and a colour map that can be used with
# matplotlib's imshow to show phase in a good looking way and on
# a white background.
norm = Normalize(vmin=-0.5, clip=False)
cmap = copy(plt.cm.get_cmap('jet'))
# White is for masking
cmap.set_bad('white', 1.0)
# Black is for unlabelled fringes
cmap.set_under('black', 1.0)
