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

import scipy as sp
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator
import matplotlib.pyplot as plt
import tkinter as Tk
import ctypes
from time import sleep
from . import graphics as m2graphics
import magic2gui.matplotlib_frame as m2mframe

# added_points = []


# This class is used to store triangulation data, including the initial
# Delaunay triangulation, points that are used to create it, a list
# of triangles and flat triangles. It's got methods used to retrieve a list
# of all the triangles (for triplot for example) and an optimise function
# that clears up flat fetures
class Triangulation:
    def __init__(self, points, canvas, status=None):
        if status is not None:
            status.set("Performing Delaunay triangulation",0)
        else:
            print("Performing Delaunay triangulation")
        # Store the points and their values
        self.points = points
        self.values = [canvas.fringe_phases[p[0], p[1]] for p in self.points]
        # Calculate the Delaunay triangulation
        self.error = False
        try:
            self.dt = Delaunay(points)
        except ValueError:
            self.error = True
            return None
        # A list of all the triangle objects
        self.triangles = []
        # A list of the flat triangles' indices
        self.flat_triangles = []
        if status is not None:
            status.set("Building data structures", 5)
        else:
            print("Building the data")
        # Create Triangle objects and add them to lists
        for i in range(len(self.dt.simplices)):
            triangle = Triangle(self.dt, i, self.points, self.values)
            if triangle.flat:
                self.flat_triangles.append(i)
            self.triangles.append(triangle)
        # Print out some stats
        if status is None:
            print("Finished")
            print("Flat triangles are {:0.2f} percent of the data".format(
                len(self.flat_triangles)/len(self.triangles)))
            print(len(self.flat_triangles), "flat triangles,",
                  len(self.triangles), "triangles in total")

    # Get a list of all the triangles. Each elements is a list of three indices
    # pointing to vertices in self.points
    def get_simplices(self):
        return [triangle.vertices for triangle in self.triangles]

    def optimise(self, status=None):
        if status is not None:
            status.set("Removing flat triangles", 15)
        else:
            print("Removing flat triangles")
        # Initial length of the flat triangle list is stored to keep track
        # of our progress
        initial_len = len(self.flat_triangles)
        # This loop will run until no further changes are possible
        changes = 1
        while changes:
            # Set the number of changes to 0. If a change is made, this
            # will be incremented, making the while loop do another round
            changes = 0
            # Instead of using a for loop, we will use a while loop with
            # our own iterator (i). This gives us more control, which
            # is necessary since the list we are iterating on changes size
            # during this operation
            i = 0
            while i < len(self.flat_triangles):
                # Get the flat triangle object in quetsion, as well as its
                # sloped neighbour (if it exists) and the vertex indices
                # for the points that do not lay on the joining edge
                triangle = self.triangles[self.flat_triangles[i]]
                neighbour, op1, op2 = triangle.get_sloped_neighbour(self)
                # If there is no sloped neighbour across a long edge, we leave
                # this flat triangle alone. It is possible that it will get a
                # sloped neighbour later in the loop. If not, the while loop
                # will break due to no changes being made, and this triangle
                # will stay in self.flat_triangles, indicating that it is
                # not fixable
                if neighbour is None:
                    i += 1
                else:
                    # Calculate the areas of the two initial triangles, and the
                    # two triangles that would be constructed in an edge flip.
                    # If the sum of the areas before and after the flip is the
                    # same, the simplex formed by the triangles was convex
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
                    # Check if the areas before and after are the same, and
                    # also whether the final areas aren't zero
                    if ai1 + ai2 == af1 + af2 and af1 != 0 and af2 != 0:
                        # If convex, and the switch is possible, flip the edge
                        self.switch_triangles(triangle, neighbour, op1, op2)
                        # We delete the triangle from the lits of flat
                        # triangles once we're done with it...
                        del self.flat_triangles[i]
                        # ...and increment the change counter
                        changes += 1
                    else:
                        # Otherwise, add a point in the middle of the line
                        # shared by the triangles
                        self.add_point(triangle, neighbour, op1, op2)
                        del self.flat_triangles[i]
                        changes += 1
            # This indicates how many flat triangles we have processed
            if status is not None:
                status.set("Removing flat triangles", 15+55*(1-len(self.flat_triangles)/initial_len))
            else:
                print(1-len(self.flat_triangles)/initial_len)

    def switch_triangles(self, triangle, neighbour, op1, op2):
        # print("switching", triangle.index, neighbour.index,
        #       "with neighbours", triangle.neighbours,
        #       neighbour.neighbours, self.triangles[29].neighbours)
        tn = triangle.neighbours.copy()
        nn = neighbour.neighbours.copy()
        # This escapes words, maybe a drawing will help?
        # https://imgur.com/ZvuKOZH
        # Basically we need to update the neighbours lists of the
        # triangles we're working with...
        triangle.neighbours[op1] = nn[
            sp.argwhere(neighbour.vertices == triangle.vertices[(op1+1) % 3])
        ]
        triangle.neighbours[(op1+2) % 3] = neighbour.index
        neighbour.neighbours[op2] = tn[(op1+2) % 3]
        neighbour.neighbours[
            sp.argwhere(neighbour.vertices == triangle.vertices[(op1+1) % 3])
        ] = triangle.index
        # ...as well as their neighbouring triangles (if they exist)
        if triangle.neighbours[op1] != -1:
            n_temp = self.triangles[triangle.neighbours[op1]].neighbours
            n_temp[
                sp.argwhere(n_temp == neighbour.index)
            ] = triangle.index
        if neighbour.neighbours[op2] != -1:
            n_temp = self.triangles[neighbour.neighbours[op2]].neighbours
            n_temp[
                sp.argwhere(n_temp == triangle.index)
            ] = neighbour.index
        # Now we just need to update the triangles' vertices
        triangle.vertices[(op1+1) % 3] = neighbour.vertices[op2]
        neighbour.vertices[
            sp.argwhere(neighbour.vertices == triangle.vertices[(op1+2) % 3])
        ] = triangle.vertices[op1]
        triangle.vert_coordinates = self.points[triangle.vertices]
        neighbour.vert_coordinates = self.points[neighbour.vertices]
        # Finally we change the status of the flat triangle,
        # as it is now sloped
        triangle.flat = False

    def add_point(self, triangle, neighbour, op1, op2):
        # The point is added in the middle of the line shared by
        # the two triangles
        new_point = sp.mean([triangle.vert_coordinates[(op1+1) % 3],
                             triangle.vert_coordinates[(op1+2) % 3]], 0)
        # print(triangle.vert_coordinates[(op1+1) % 3],
        #       triangle.vert_coordinates[(op1+2) % 3], new_point)
        # added_points.append(new_point)
        # The point's value is calculated with a variation on linear
        # interpolation of George's design. It seems to produce
        # reasonable values
        d1 = sp.sqrt(sp.sum((new_point-sp.array(triangle.vert_coordinates[(op1+1)%3]))**2, 0))
        d2 = sp.sqrt(sp.sum((new_point-sp.array(neighbour.vert_coordinates[op2]))**2, 0))
        new_value = (d2*self.values[triangle.vertices[(op1+1) % 3]]
                     + d1*self.values[neighbour.vertices[op2]])/(d1+d2)
        new_index = len(self.points)
        self.points = sp.append(self.points, [new_point], 0)
        self.values = sp.append(self.values, [new_value], 0)
        # Change the triangulation to include the new point
        # A drawing is helpful in understanding what is happening here
        # https://imgur.com/5uUkYz4
        # Start by creating two new, placeholder triangles
        t2 = TriangleCopy(len(self.triangles), self.points,
                          triangle.vertices, triangle.neighbours)
        self.triangles.append(t2)
        n2 = TriangleCopy(len(self.triangles), self.points,
                          neighbour.vertices, neighbour.neighbours)
        self.triangles.append(n2)
        # Now change the neighbours
        triangle.neighbours[(op1+2) % 3] = t2.index
        neighbour.neighbours[
            sp.argwhere(neighbour.vertices == triangle.vertices[(op1+2) % 3])
        ] = n2.index
        t2.neighbours[op1] = n2.index
        t2.neighbours[(op1+1) % 3] = triangle.index
        n2.neighbours[op2] = t2.index
        n2.neighbours[
            sp.argwhere(neighbour.vertices == triangle.vertices[(op1+2) % 3])
        ] = neighbour.index
        if t2.neighbours[(op1+2) % 3] != -1:
            n_temp = self.triangles[t2.neighbours[(op1+2) % 3]].neighbours
            n_temp[
                sp.argwhere(n_temp == triangle.index)
            ] = t2.index
        arg = int(sp.argwhere(neighbour.vertices == triangle.vertices[(op1+2) % 3]))
        if n2.neighbours[arg] != -1:
            n_temp = self.triangles[t2.neighbours[arg]].neighbours
            n_temp[
                sp.argwhere(n_temp == neighbour.index)
            ] = n2.index
        # Now update the vertices
        # A copy is created as we change the triangle's vertices, but we
        # still need the original state for reference
        tv = triangle.vertices.copy()
        triangle.vertices[(op1+1) % 3] = new_index
        neighbour.vertices[
            sp.argwhere(neighbour.vertices == tv[(op1+1) % 3])
        ] = new_index
        t2.vertices[(op1+2) % 3] = new_index
        n2.vertices[
            sp.argwhere(n2.vertices == tv[(op1+2) % 3])
        ] = new_index
        triangle.vert_coordinates = self.points[triangle.vertices]
        neighbour.vert_coordinates = self.points[neighbour.vertices]
        t2.vert_coordinates = self.points[t2.vertices]
        n2.vert_coordinates = self.points[n2.vertices]
        # Finally mark the triangle as sloped
        triangle.flat = False

    # Interpolate the data based on the calculated triangulation
    def interpolate(self, canvas, status=None):
        # Clear the interpolated canvas
        canvas.interpolated = sp.zeros_like(canvas.fringes_image)-1024.0
        if status is not None:
            status.set("Performing the interpolation", 70)
        else:
            print("Performing the interpolation")
        # Iterate over all the triangles in the triangulation
        for triangle in self.triangles:
            # Create a shortcut to the triangle's vertices
            co = triangle.vert_coordinates
            # Calculate a few constants for the Barycentric Coordinates
            # More info: https://codeplea.com/triangular-interpolation
            div = (co[1,0]-co[2,0])*(co[0,1]-co[2,1])+(co[2,1]-co[1,1])*(co[0,0]-co[2,0])
            a0 = (co[1, 0]-co[2, 0])
            a1 = (co[2, 1]-co[1, 1])
            a2 = (co[2, 0]-co[0, 0])
            a3 = (co[0, 1]-co[2, 1])
            # Calculate the bounds of a rectangle that fully encloses
            # the current triangle
            xmin = int(sp.amin(triangle.vert_coordinates[:,1]))
            xmax = int(sp.amax(triangle.vert_coordinates[:,1]))+1
            ymin = int(sp.amin(triangle.vert_coordinates[:,0]))
            ymax = int(sp.amax(triangle.vert_coordinates[:,0]))+1
            # Take out slices of the x and y arrays,
            # containing the points' coordinates
            x_slice = canvas.x[ymin:ymax, xmin:xmax]
            y_slice = canvas.y[ymin:ymax, xmin:xmax]
            # Use Barycentric Coordinates and the magic of numpy (scipy in this
            # case) to perform the calculations with the C backend, instead
            # of iterating on pixels with Python loops.
            # If you have not worked with numpy arrays befor dear reader,
            # the idea is that if x = [[0 1]
            #                          [2 3]],
            # then x*3+1 is a completely valid operation, returning
            # x = [[1 4]
            #      [7 10]]
            # Basically, we can do maths on arrays as if they were variables.
            # Convenient, and really fast!
            w0 = (a0*(x_slice-co[2,1])+a1*(y_slice-co[2,0]))/div
            w1 = (a2*(x_slice-co[2,1])+a3*(y_slice-co[2,0]))/div
            w2 = sp.round_(1-w0-w1, 10)
            # Calculate the values for a rectangle enclosing our triangle
            slice = (
                self.values[triangle.vertices[0]]*w0
                + self.values[triangle.vertices[1]]*w1
                + self.values[triangle.vertices[2]]*w2
            )
            # Make a mask (so that we only touch the points
            # inside of the triangle).
            # In Barycentric Coordinates the points outside of the triangle
            # have at least one of the coefficients negative, so we use that
            mask = sp.logical_and(sp.logical_and(w0 >= 0, w1 >= 0), w2 >= 0)
            # Change the points in the actual canvas
            canvas.interpolated[ymin:ymax, xmin:xmax][mask] = slice[mask]
        canvas.interpolation_done = True


# Calculate the distance between two points in the points list
def distance(points, i1, i2):
    return sp.sqrt((points[i2, 0]-points[i1, 0])**2
                   + (points[i2, 1]-points[i1, 1])**2)


# A class representing a triangle
class Triangle:
    # Tell Python what properties so that it can manage RAM more efficiently
    __slots__ = ['vertices', 'vert_coordinates', 'neighbours', 'index',
                 'flat', 'long_edges']

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
                    return neighbour, i, int(
                        sp.argwhere(neighbour.neighbours == self.index)
                    )
        # If no neighbour found, return None three times, to make the return
        # length consistent
        return None, None, None


# A copy of the Triangle class with a different constructor. Useful
# when creating new triangles that do not relay on the Delaunay
# triangulation
class TriangleCopy(Triangle):
    __slots__ = ['vertices', 'vert_coordinates', 'neighbours', 'index',
                 'flat', 'long_edges']

    def __init__(self, index, points, vertices, neighbours):
        # Making copies is absolutely necessary due to the way Python
        # handles lists - the variable is actually a pointer, so if we just
        # used self.vertices = vertices.copy, we would be changing the original
        # list every time we made changes to the new triangle
        self.vertices = vertices.copy()
        self.vert_coordinates = points[self.vertices]
        self.neighbours = neighbours.copy()
        self.index = index
        # The created triangle will be sloped by definition
        self.flat = False
        self.long_edges = [True, True, True]


# This is the main interpolation method, using a special algorithm to
# remove all flat triangles that are possible to remove
def triangulate(canvas, ax, status):
    # Create a Triangulation object
    tri = Triangulation(sp.transpose(
                        sp.nonzero(canvas.fringes_image_clean)),
                        canvas, status)
    # Check if an error has been encountered (this would be due to the
    # user not labelling any fringes)
    if tri.error:
        return None
    else:
        # If the triangulation was succesfull, optimise it...
        tri.optimise(status)
        # ...and perform the interpolation
        tri.interpolate(canvas, status)
        status.set("Done", 100)
        return True


# This is a quick interpolation method that does not bother with fixing
# flat triangles. It uses standard scipy functions, which makes it faster
def fast_tri(canvas, ax, status):
    if status is not None:
        status.set("Creating the interpolant", 0)
    # Create a list of the points for the triangulation
    points = sp.transpose(sp.nonzero(canvas.fringes_image_clean))
    try:
        # Create an interpolation object. The second argument is a list
        # of values for all the supplied points
        interpolation = LinearNDInterpolator(points, [canvas.fringe_phases[p[0], p[1]] for p in points], fill_value=-1024.0)
        status.set("Calculating values for points on canvas", 60)
        # This calls the interpolant's calculating function and returns values
        # for every point on the canvas. This is then reshaped to fit the
        # original image
        canvas.interpolated = sp.reshape(interpolation.__call__([canvas.xy]), canvas.fringes_image.shape)
        canvas.interpolation_done = True
        status.set("Done", 100)
        return True
    except ValueError:
        # This will happen if no fringes were labelled
        return None


# Here be dragons
# On a more serious note, this function was used while creating this software.
# It didn't have a GUI, so this just displays output in separate matplotlib
# windows. Potentially useful for debugging purposes, so left as an option.
def triangulate_debug(canvas, options=None):
    print("### Starting interpolation in debug mode ###")
    # Depending on whether we are in GUI mode or not, we will use the
    # matplotlib.pyplot library directly, or through the DebugWindow interface
    # (defined below), which wraps the graphs in a tkinter window. This is
    # necessary as tkinter doesn't play well with matplotlib windows and
    # plt.show() would not stop execution until the main Magic2 windows is
    # closed (and that's not very useful). By redefining plt we are able to
    # leave the code in this function alone, so that it still works in
    # headless mode (with main_old.py)
    global plt
    if options is not None:
        plt = DebugWindow(options)
    tri = Triangulation(sp.transpose(
                        sp.nonzero(canvas.fringes_image_clean)),
                        canvas)
    plt.imshow(canvas.fringes_image_clean, cmap=m2graphics.cmap)
    # Plot the triangulation. Flat triangles will be green
    plt.triplot(tri.points[:, 1], tri.points[:, 0], tri.get_simplices())
    plt.triplot(tri.points[:, 1], tri.points[:, 0], [tri.triangles[i].vertices for i in tri.flat_triangles])
    plt.show()
    # plt.triplot(tri.points[:, 1], tri.points[:, 0], tri.dt.simplices)
    print("Optimisation")
    tri.optimise()
    print("Finished")
    # Plot the optimised triangulation. Flat triangles will be green
    plt.imshow(canvas.fringe_phases, cmap=m2graphics.cmap)
    # print(tri.flat_triangles)
    # print(added_points)
    # plt.triplot(tri.points[:, 1], tri.points[:, 0], [tri.triangles[i].vertices for i in tri.flat_triangles])
    plt.triplot(tri.points[:, 1], tri.points[:, 0], tri.get_simplices())
    plt.triplot(tri.points[:, 1], tri.points[:, 0], [tri.triangles[i].vertices for i in tri.flat_triangles])
    plt.show()
    # Perform interpolation
    print("Interpolating")
    tri.interpolate(canvas)
    plt.imshow(sp.ma.masked_where(sp.logical_or(canvas.mask == False, canvas.interpolated==-1024.0), canvas.interpolated), cmap=m2graphics.cmap)
    plt.show()
    plt.imshow(sp.ma.masked_where(sp.logical_or(canvas.mask == False, canvas.interpolated==-1024.0), canvas.interpolated), cmap=m2graphics.cmap)
    plt.triplot(tri.points[:, 1], tri.points[:, 0], tri.get_simplices())
    plt.show()


# A helper class that is used instead of matplotlib.pyplot to render output of
# interpolate_debug()
class DebugWindow:
    def __init__(self, options):
        # Save a reference to the options object
        self.options = options
        # Define a placeholder for self.window
        self.window = None

    def make_window(self):
        # Create a window for the graph
        window = self.window = Tk.Toplevel()
        window.wm_title("Debug mode interpolation")
        # This is windows specific, but needed for the icon to show up
        # in the taskbar. try/catch in case this is run on other platforms
        try:
            myappid = 'jdranczewski.magic2'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
        # Setting the icon doesn't work on Linux for some reason, so we have
        # a try/catch here again
        try:
            window.iconbitmap("magic2.ico")
        except:
            pass
        # Set the focus to the new window
        # Pin to the root window
        self.window.transient(self.options.root)
        window.focus_set()
        window.geometry("+%d+%d" % (self.options.root.winfo_rootx()+50,
                                    self.options.root.winfo_rooty()+50))
        # Create the matplotlib frame
        self.mframe = m2mframe.GraphFrame(window, bind_keys=True,
                                          show_toolbar=True)
        self.mframe.pack(fill=Tk.BOTH, expand=1)
        # Create a variable that will be used to stop code execution until the
        # window is closed
        self.proceed = False
        window.protocol("WM_DELETE_WINDOW", self.stop)

    def stop(self):
        # Signal that we can proceed now
        self.proceed = True
        # Set the focus back to the main window
        self.options.root.focus_set()
        # Destroy the graph's window
        self.window.destroy()
        # Signal
        self.window = None

    # imshow and triplot correspond to matplotlib's functions, but use the
    # mframe in self.window for drawings
    def imshow(self, *args, **kwargs):
        if self.window is None:
            # A windows is created if not allready there
            self.make_window()
        self.mframe.ax.imshow(*args, **kwargs)

    def triplot(self, *args, **kwargs):
        if self.window is None:
            self.make_window()
        self.mframe.ax.triplot(*args, **kwargs)

    # This refreshes the mframe's canvas and waits for self.proceed to continue
    # execution and allow the triangulation code to continue
    def show(self):
        self.mframe.fig.canvas.draw()
        while not self.proceed:
            self.window.update()
            # Bit of a hack, but works
            sleep(0.25)
        self.proceed = False
        self.mframe.ax.clear()
