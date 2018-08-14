import scipy as sp
from scipy.spatial import Delaunay
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt
from . import graphics as m2graphics


# This class is used to store triangulation data, including the initial
# Delaunay triangulation, points that are used to create it, a list
# of triangles and flat triangles. It's got methods used to retrieve a list
# of all the triangles (for triplot for example) and an optimise function
# that clears up flat fetures
class Triangulation:
    def __init__(self, points, canvas):
        # Store the points and their values
        self.points = points
        self.values = [canvas.fringe_phases[p[0], p[1]] for p in self.points]
        print("Starting triangulation")
        # Calculate the Delaunay triangulation
        self.dt = Delaunay(points)
        # Two lists of Triangle objects, one for all of them and one for
        # the flat ones
        self.triangles = []
        self.flat_triangles = []
        print("Building the data")
        # Create Triangle objects and add them to lists
        for i in range(len(self.dt.simplices)):
            triangle = Triangle(self.dt, i, self.points, self.values)
            if triangle.flat:
                self.flat_triangles.append(i)
            self.triangles.append(triangle)
        print("Finished")
        # Print out some stats
        print(len(self.flat_triangles)/len(self.triangles))
        print(len(self.flat_triangles), len(self.triangles))

    # Get a list of all the triangles. Each elements is a list of three indices
    # pointing to vertices in self.points
    def get_simplices(self):
        return self.dt.simplices

    def optimise(self):
        changes = 1
        while changes:
            changes = 0
            i = 0
            while i < len(self.flat_triangles):
                triangle = self.triangles[self.flat_triangles[i]]
                neighbour, op1, op2 = triangle.get_sloped_neighbour(self)
                if neighbour is None:
                    print("none")
                    # del self.flat_triangles[i]
                    i += 1
                else:
                    # all_points = sp.concatenate(
                    #     (self.points[triangle.vertices, :],
                    #      self.points[neighbour.vertices, :]), 0)
                    # ch = len(ConvexHull(all_points).vertices)
                    ch = 4
                    ai1 = 0.5 * abs(
                          (triangle.vert_coordinates[op1, 1] - triangle.vert_coordinates[(op1+2)%3, 1])
                        * (triangle.vert_coordinates[(op1+1)%3, 0] - triangle.vert_coordinates[op1, 0])
                        - (triangle.vert_coordinates[op1, 1] - triangle.vert_coordinates[(op1+1)%3, 1])
                        * (triangle.vert_coordinates[(op1+2)%3, 0] - triangle.vert_coordinates[op1, 0])
                    )
                    ai2 = 0.5 * abs(
                          (neighbour.vert_coordinates[op2, 1] - neighbour.vert_coordinates[(op2+2)%3, 1])
                        * (neighbour.vert_coordinates[(op2+1)%3, 0] - neighbour.vert_coordinates[op2, 0])
                        - (neighbour.vert_coordinates[op2, 1] - neighbour.vert_coordinates[(op2+1)%3, 1])
                        * (neighbour.vert_coordinates[(op2+2)%3, 0] - neighbour.vert_coordinates[op2, 0])
                    )
                    af1 = 0.5 * abs(
                          (triangle.vert_coordinates[op1, 1] - triangle.vert_coordinates[(op1+2)%3, 1])
                        * (neighbour.vert_coordinates[op2, 0] - triangle.vert_coordinates[op1, 0])
                        - (triangle.vert_coordinates[op1, 1] - neighbour.vert_coordinates[op2, 1])
                        * (triangle.vert_coordinates[(op1+2)%3, 0] - triangle.vert_coordinates[op1, 0])
                    )
                    af2 = 0.5 * abs(
                          (triangle.vert_coordinates[op1, 1] - triangle.vert_coordinates[(op1+1)%3, 1])
                        * (neighbour.vert_coordinates[op2, 0] - triangle.vert_coordinates[op1, 0])
                        - (triangle.vert_coordinates[op1, 1] - neighbour.vert_coordinates[op2, 1])
                        * (triangle.vert_coordinates[(op1+1)%3, 0] - triangle.vert_coordinates[op1, 0])
                    )
                    # print(ai1, ai2, af1, af2)
                    if ai1 + ai2 == af1 + af2:
                        print("convex")
                        # del self.flat_triangles[i]
                        i += 1
                    else:
                        # print("concave")
                        # del self.flat_triangles[i]
                        i += 1


# Calculate the distance between two points in the points list
def distance(points, i1, i2):
    return sp.sqrt((points[i2, 0]-points[i1, 0])**2
                   + (points[i2, 1]-points[i1, 1])**2)


# A class representing a triangle
class Triangle:
    def __init__(self, dt, index, points, values):
        # Copy the vertex and neighbours info
        self.vertices = dt.simplices[index]
        self.vert_coordinates = points[self.vertices]
        self.neighbours = dt.neighbors[index]
        self.index = index
        # Check whether the triangle is flat
        self.flat = (values[self.vertices[0]] == values[self.vertices[1]]
                     and values[self.vertices[1]] == values[self.vertices[2]])
        if self.flat:
            # If the triangle is flat, it is important to check which of the
            # edges are not parts of the contour - we can flip those without
            # getting lines that cut the contours. The contour lines are always
            # sqrt(2) or shorter
            self.long_edges = [
                distance(points, self.vertices[1], self.vertices[2]) > sp.sqrt(2),
                distance(points, self.vertices[2], self.vertices[0]) > sp.sqrt(2),
                distance(points, self.vertices[0], self.vertices[1]) > sp.sqrt(2)]
            # If none of the edges is longer than sqrt(2), the triangle lies
            # within the contour and it doesn't make sense to fix it.
            self.flat = self.flat and sp.count_nonzero(self.long_edges)
        # This will not be used, but assign a value for consistency
        else:
            self.long_edges = [True, True, True]

    # This function returns the first found sloped neighbour of the triangle.
    # It only checks for neighbours that share one of the long edges, so as
    # to not cut through contours
    def get_sloped_neighbour(self, tri):
        for i in range(3):
            # If the edge is long
            if self.long_edges[i]:
                n_index = self.neighbours[i]
                # If the neighbour exists and isn't flat, return its index
                if n_index != -1 and not tri.triangles[n_index].flat:
                    neighbour = tri.triangles[n_index]
                    return neighbour, i, sp.argwhere(neighbour.neighbours == self.index)
        # If no neighbour found, return None
        return None, None, None


def triangulate(canvas):
    tri = Triangulation(sp.transpose(
                        sp.nonzero(canvas.fringes_image)),
                        canvas)
    plt.imshow(canvas.fringe_phases, cmap=m2graphics.cmap)
    plt.triplot(tri.points[:, 1], tri.points[:, 0], tri.get_simplices())
    plt.triplot(tri.points[:, 1], tri.points[:, 0], [tri.triangles[i].vertices for i in tri.flat_triangles])
    plt.show()
    print("Optimisation")
    tri.optimise()
    print("Finished")
    plt.imshow(canvas.fringe_phases, cmap=m2graphics.cmap)
    plt.triplot(tri.points[:, 1], tri.points[:, 0], tri.get_simplices())
    print(tri.flat_triangles)
    plt.triplot(tri.points[:, 1], tri.points[:, 0], [tri.triangles[i].vertices for i in tri.flat_triangles])
    plt.show()
