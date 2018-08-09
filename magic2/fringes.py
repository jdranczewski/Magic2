# This file contains functionality related to dealing with fringes
import numpy as np
import matplotlib.pyplot as plt


class Fringes():
    def __init__(self):
        # Max is the maximum phase index
        self.max = 0
        # List is a list of pointers to particular fringes
        self.list = []


class Fringe():
    def __init__(self, points):
        # List of points in the fringe
        self.points = points
        # Phase is an integer, going from 0 up
        self.phase = 0


def read_fringes(fringes, fringes_image):
    # Create a list of coordinates of all the black pixels
    # Note that the coordinates will be in the order [y, x]
    # as this is the convention used for matrices: [row, column].
    black_points = np.transpose(np.nonzero(fringes_image))
    # While there are still points to process
    plt.imshow(fringes_image)
    while len(black_points):
        # Create an array to store the points of this fringe
        point = black_points[0]
        points = [point]
        # Remove in the point so that it is not analysed again
        fringes_image[point[0], point[1]] = False
        # Find the point's neighbours
        neigbours = np.transpose(np.nonzero(
                    fringes_image[point[0]-1:point[0]+2,
                                  point[1]-1:point[1]+2]))
        # While we still can find any neighbours, add them to the list
        while len(neigbours):
            if len(neigbours) > 1:
                # Store for later backtarcking
                pass
            # The neighbours list contains relative coordinates,
            # we need to offset them
            point = [neigbours[0, 0] + point[0] - 1,
                      neigbours[0, 1] + point[1] - 1]
            points.append(point)
            fringes_image[point[0], point[1]] = False
            neigbours = np.transpose(np.nonzero(
                        fringes_image[point[0]-1:point[0]+2,
                                      point[1]-1:point[1]+2]))
        points = np.array(points)
        # plt.plot(points[:,1], points[:,0])
        black_points = np.transpose(np.nonzero(fringes_image))
    plt.show()
