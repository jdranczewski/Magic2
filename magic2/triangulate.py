import scipy as sp
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
from . import graphics as m2graphics


class Triangulation:
    def __init__(self, points, canvas):
        self.points = points
        self.values = [canvas.fringe_phases[p[0], p[1]] for p in self.points]
        print("Starting triangulation")
        self.dt = Delaunay(points)
        self.triangles = []
        self.flat_triangles = []
        print("Building the data")
        for i in range(len(self.dt.simplices)):
            triangle = Triangle(self.dt, i, self.points, self.values)
            if triangle.flat:
                self.flat_triangles.append(i)
            self.triangles.append(triangle)
        print("Finished")
        print(len(self.flat_triangles)/len(self.triangles))
        print(len(self.flat_triangles), len(self.triangles))

    def get_simplices(self):
        return self.dt.simplices


def distance(points, i1, i2):
    return sp.sqrt((points[i2, 0]-points[i1, 0])**2
                   + (points[i2, 1]-points[i1, 1])**2)


class Triangle:
    def __init__(self, dt, index, points, values):
        self.vertices = dt.simplices[index]
        self.neighbours = dt.neighbors[index]
        self.flat = (values[self.vertices[0]] == values[self.vertices[1]]
                     and values[self.vertices[1]] == values[self.vertices[2]])
        if self.flat:
            self.long_edges = [
                distance(points, self.vertices[1], self.vertices[2]) > sp.sqrt(2),
                distance(points, self.vertices[2], self.vertices[0]) > sp.sqrt(2),
                distance(points, self.vertices[0], self.vertices[1]) > sp.sqrt(2)]
            self.flat = self.flat and sp.count_nonzero(self.long_edges)
        else: self.long_edges = [True, True, True]

    def get_sloped_neighbour(self, tri):
        for i in range(3):
            if self.long_edges[i]:
                n_index = self.neighbours[i]
                if not tri.triangles[n_index].flat:
                    return n_index
        return None


def triangulate(canvas):
    tri = Triangulation(sp.transpose(
                        sp.nonzero(canvas.fringes_image)),
                        canvas)
    plt.imshow(canvas.fringe_phases, cmap=m2graphics.cmap)
    plt.triplot(tri.points[:, 1], tri.points[:, 0], tri.get_simplices())
    plt.triplot(tri.points[:, 1], tri.points[:, 0], [tri.triangles[i].vertices for i in tri.flat_triangles])
    plt.show()
