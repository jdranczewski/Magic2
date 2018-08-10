import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from copy import copy


# This function can be used to draw the fringes on a given canvas
# at a specified line width. 'fringes' is a Fringes object.
def render_fringes(fringes, canvas, width=1):
    # Hovewer nasty this nested loop looks, it allows us to easily iterate
    # over all points in all fringes. The x range and y range are also
    # executed only once if width is 0
    for fringe in fringes.list:
        for point in fringe.points:
            colour = 1
            for x in range(-width+1, width):
                for y in range(-width+1, width):
                    # This try...excpt saves us from problems with running out
                    # of canvas space while alerting us of other valid errors
                    # that could occur
                    try:
                        canvas[point[0]+y, point[1]+x] = colour
                    except IndexError:
                        pass

# Define a normalization and a colour map that can be used with
# matplotlib's imshow to show phase in a good looking way and on
# a white background.
norm = Normalize(vmin=0, clip=False)
cmap = copy(plt.cm.get_cmap('jet'))
cmap.set_under('white')
