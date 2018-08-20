import scipy as sp
import scipy.special as special
from . import graphics as m2graphics


# This class stores some data about the current labelling operation
class Labeller():
    def __init__(self):
        # List of the points of the line being drawn
        self.points = []
        # Is the control key pressed?
        self.control = False
        # IDs of the events attached to the figure
        self.binds = []


# This function is used to handle the user pressing a mouse key
# while in the graphing area
def onclick(event, labeller, line_plot, fringes, canvas, fig, ax):
    # If this was a single click within the graphing area, add a point
    # to the line
    if labeller.control and not event.dblclick and event.xdata:
        labeller.points.append([event.ydata, event.xdata])
        # We use the points list to draw a line on the graph
        points = sp.array(labeller.points)
        line_plot.set_data(points[:, 1], points[:, 0])
        line_plot.figure.canvas.draw()
        # If the event was a double click, label the fringes and clear the data
        # related to the current labelling operation
        if event.button == 3:
            label_fringes(labeller, fringes, canvas, fig, ax)
            labeller.points = []
            line_plot.set_data([], [])
            line_plot.figure.canvas.draw()


# This uses the set of points chosen by the user to label the fringes
def label_fringes(labeller, fringes, canvas, fig, ax):
    # Create two empty lists of x and y coordinates that we will be
    # iterating over
    x = []
    y = []
    # For every pair of points chosen by the user, create a set of pixels
    # to check that goes in a line between them
    for i in range(1, len(labeller.points)):
        # The resolution is set to be the larger of the two x or y intervals,
        # some coordinates in the other direction will be repeated.
        # The line may for example go
        #           ##
        #             ###
        #                ##
        resolution = int(sp.amax([abs(labeller.points[i-1][1]-labeller.points[i][1]),
                                  abs(labeller.points[i-1][0]-labeller.points[i][0])]))
        x = sp.append(x, special.round(sp.linspace(labeller.points[i-1][1],
                                                   labeller.points[i][1],
                                                   resolution)))
        y = sp.append(y, special.round(sp.linspace(labeller.points[i-1][0],
                                                   labeller.points[i][0],
                                                   resolution)))
    # Prepare for labelling. Phase and prev_index are temporarily set to -1
    phase = -1
    prev_index = -1
    # This is an array of all the changed fringes, used to render only the
    # necessary fringes (as this is the operation that incurs the most
    # overhead here)
    fix_indices = []
    # Iterate over all the points calculated previously
    for i in range(len(x)):
        # Check a range of points to make sure we are not slipping through
        # the pixels of a fringe like so:
        #      0  #
        #      0##         0 - fringe
        #     ##0          # - line
        #    #  0
        for index in canvas.fringe_indices[int(y[i])-1:int(y[i])+1, int(x[i])]:
            # If a non-empty index found, use this and break
            if index != -1:
                break
        # If the index is not -1 and not the same as the previous one, assign
        # a calculated phase to a fringe
        if index >= 0 and index != prev_index:
            if phase >= 0:
                phase += 1
                fringes.list[index].phase = phase
            else:
                # This takes the value of the first fringe encountered.
                # All values after that are just increments
                phase = fringes.list[index].phase
                if phase == -2048:
                    phase = 0
                    fringes.list[index].phase = phase
            fix_indices.append(index)
            # Storing this allows us to prevent labelling a fringe
            # multiple times
            prev_index = index
    # If the maximum phase reached in this labelling series is higher than
    # the one stored, update that. This is used to update the colour range
    if phase > fringes.max:
        fringes.max = phase
    # Render and show the changed fringes
    m2graphics.render_fringes(fringes, canvas, width=3, indices=fix_indices)
    canvas.imshow.set_data(sp.ma.masked_where(canvas.fringe_phases_visual == -1024, canvas.fringe_phases_visual))
    canvas.imshow.set_clim(0, fringes.max)
    canvas.imshow.figure.canvas.draw()
    # This (when uncommented) allows one to see the pixels the labelling line
    # went through. Useful for debugging
    # ax.plot(x,y)


# If the mouse moves in the graph area and a line has begun, make a part
# of the line move after the mouse
def onmove(event, labeller, line_plot):
    if len(labeller.points) and event.ydata:
        # Note that we are not actually modifying labeller.points here
        points = sp.append(sp.array(labeller.points),
                           [[event.ydata, event.xdata]], 0)
        line_plot.set_data(points[:, 1], points[:, 0])
        line_plot.figure.canvas.draw()


# Store whether the control key is pressed
def onpress(event, labeller, line_plot):
    if event.key == 'control':
        labeller.control = True
    elif event.key == 'backspace':
        # This deletes the point that has been placed last
        labeller.points = labeller.points[:-1]
        # If there are points to display, display them. If not,
        # set the data to empty lists
        if len(labeller.points):
            points = sp.array(labeller.points)
            line_plot.set_data(points[:, 1], points[:, 0])
        else:
            line_plot.set_data([], [])
        line_plot.figure.canvas.draw()


def onrelease(event, labeller):
    if event.key == 'control':
        labeller.control = False


# This sets up the labeller object, the line that is drawn, as well as
# attaches all the event handlers
def label(fringes, canvas, fig, ax):
    labeller = Labeller()
    line_plot, = ax.plot([], [], "--")
    b0 = fig.canvas.mpl_connect('button_press_event',
                                lambda event: onclick(event, labeller, line_plot,
                                                 fringes, canvas, fig, ax))
    b1 = fig.canvas.mpl_connect('motion_notify_event',
                                lambda event: onmove(event, labeller, line_plot))
    b2 = fig.canvas.mpl_connect('key_press_event',
                                lambda event: onpress(event, labeller, line_plot))
    b3 = fig.canvas.mpl_connect('key_release_event',
                                lambda event: onrelease(event, labeller))
    labeller.binds = [b0, b1, b2, b3]
    return labeller


def stop_labelling(fig, labeller):
    for bind in labeller.binds:
        fig.canvas.mpl_disconnect(bind)
    del labeller
