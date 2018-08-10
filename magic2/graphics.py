import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from copy import copy


def render_fringes(fringes, canvas, width=1):
    for fringe in fringes.list:
        for point in fringe.points:
            colour = 1
            for x in range(-width+1, width):
                for y in range(-width+1, width):
                    try:
                        canvas[point[0]+y, point[1]+x] = colour
                    except:
                        pass

# Define a normalization and a colour map that can be used with
# matplotlib's imshow to show phase in a good looking way and on
# a white background.
norm = Normalize(vmin=0, clip=False)
cmap = copy(plt.cm.get_cmap('jet'))
cmap.set_under('white')
