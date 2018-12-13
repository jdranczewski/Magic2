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

# This file contains functionality related to dealing with fringes
import scipy as sp
import matplotlib.pyplot as plt


class Fringes():
    def __init__(self):
        # Max is the maximum phase
        self.max = 0
        # Min is the minimum phase
        self.min = 0
        # List is a list of pointers to particular fringes
        self.list = []


class Fringe():
    def __init__(self, points, index):
        # List of points in the fringe
        self.points = points
        # Phase is an integer, going from 0 up. -2048 indicates
        # an unlabelled fringe
        self.phase = -2048
        # Store the fringe's index in the main fringe list
        self.index = index


# read_fringes takes in a Fringes class object, an True-False map
# representation of the interferogram (where Truths are the Fringe
# pixels) and an optional graph parameter that determines whether
# results should be plotted (useful for debugging). Filter is the
# minimum length a fringe should have to be detected
def read_fringes(fringes, canvas, graph=False, filter=5, phases=None):
    # Pad the image with zeroes on each edge. This solves the issue
    # of searching for neighbours and reaching beyond the edges
    # without being too complicated. This is later accounted for
    # when saving point coordinates
    fringes_image = sp.pad(canvas.fringes_image, 1, 'constant')
    # Create a list of coordinates of all the black pixels
    # Note that the coordinates will be in the order [y, x]
    # as this is the convention used for matrices: [row, column].
    black_points = sp.transpose(sp.nonzero(fringes_image))
    # While there are still points to process
    if graph:
        plt.imshow(fringes_image)
    fringe_index = -1
    while len(black_points):
        # Create an array to store the points of this fringe
        point = black_points[0]
        points = [[point[0]-1, point[1]-1]]
        # Create a list of points that need to be checked out later
        backtrack = []
        # Remove in the point so that it is not analysed again
        fringes_image[point[0], point[1]] = False
        # Find the point's neighbours
        neighbours = sp.transpose(sp.nonzero(
                    fringes_image[point[0]-1:point[0]+2,
                                  point[1]-1:point[1]+2]))
        # While we still can find any neighbours, add them to the list
        while len(neighbours):
            # If there are any additional points, store them. We will come
            # back to them. They have to be earsed to, so that we do not visit
            # the twice
            for additional_point in neighbours[1:]:
                backtrack.append([additional_point[0] + point[0] - 1,
                                  additional_point[1] + point[1] - 1])
                fringes_image[additional_point[0] + point[0] - 1,
                              additional_point[1] + point[1] - 1] = False
            # The neighbours list contains relative coordinates,
            # we need to offset them and then add the point to
            # out points list
            point = [neighbours[0, 0] + point[0] - 1,
                     neighbours[0, 1] + point[1] - 1]
            # This accounts for the padding introduced earlier
            points.append([point[0]-1, point[1]-1])
            fringes_image[point[0], point[1]] = False
            # Find the neighbours of the new point
            neighbours = sp.transpose(sp.nonzero(
                        fringes_image[point[0]-1:point[0]+2,
                                      point[1]-1:point[1]+2]))
            # If the point has no neighbours, try pulling a point out of the
            # backtracking list
            if not len(neighbours) and len(backtrack):
                point = backtrack[0]
                backtrack = backtrack[1:]
                neighbours = sp.array([[1, 1]])
        # Create a fringe obejct and append it to the fringe list
        if len(points) >= 5:
            fringe_index += 1
            fringe = Fringe(points, fringe_index)
            # This uses a previously created phase list (for example from
            # an .m2 file)
            if phases is not None:
                fringe.phase = phases[fringe_index]
            fringes.list.append(fringe)
            if graph:
                points = sp.array(points)
                plt.plot(points[:, 1], points[:, 0])
        black_points = sp.transpose(sp.nonzero(fringes_image))
    if graph:
        plt.show()
