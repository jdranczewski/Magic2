import numpy as np
import magic2.graphics as m2graphics


class Labeller():
    def __init__(self):
        self.points = []
        self.control = False


def onclick(event, labeller, line_plot, fringes, canvas, fig, ax):
    if labeller.control and not event.dblclick and event.xdata:
        labeller.points.append([event.ydata, event.xdata])
        points = np.array(labeller.points)
        line_plot.set_data(points[:, 1], points[:, 0])
        line_plot.figure.canvas.draw()
    elif event.dblclick:
        label_fringes(labeller, fringes, canvas, fig, ax)
        labeller.points = []
        line_plot.set_data([], [])
        line_plot.figure.canvas.draw()


def label_fringes(labeller, fringes, canvas, fig, ax):
    x = []
    y = []
    for i in range(1, len(labeller.points)):
        resolution = int(np.max([abs(labeller.points[i-1][1]-labeller.points[i][1]),
                                 abs(labeller.points[i-1][0]-labeller.points[i][0])]))
        x = np.append(x, np.round(np.linspace(labeller.points[i-1][1],
                                              labeller.points[i][1],
                                              resolution)))
        y = np.append(y, np.round(np.linspace(labeller.points[i-1][0],
                                              labeller.points[i][0],
                                              resolution)))
    phase = -1
    for i in range(len(x)):
        index = canvas.fringe_indices[int(y[i]), int(x[i])]
        if index >= 0:
            if phase >= 0:
                phase += 1
                fringes.list[index].phase = phase
            else:
                phase = fringes.list[index].phase
    m2graphics.render_fringes(fringes, canvas, width=3)
    canvas.imshow.set_data(canvas.fringe_phases_visual)
    ax.plot(x,y)


def onmove(event, labeller, line_plot):
    if len(labeller.points) and event.ydata:
        points = np.append(np.array(labeller.points),
                           [[event.ydata, event.xdata]], 0)
        line_plot.set_data(points[:, 1], points[:, 0])
        line_plot.figure.canvas.draw()


def onpress(event, labeller):
    if event.key == 'control':
        labeller.control = True


def onrelease(event, labeller):
    if event.key == 'control':
        labeller.control = False


def label(fringes, canvas, fig, ax):
    labeller = Labeller()
    line_plot, = ax.plot([], [], "--")
    fig.canvas.mpl_connect('button_press_event',
                           lambda event: onclick(event, labeller, line_plot,
                                                 fringes, canvas, fig, ax))
    fig.canvas.mpl_connect('motion_notify_event',
                           lambda event: onmove(event, labeller, line_plot))
    fig.canvas.mpl_connect('key_press_event',
                           lambda event: onpress(event, labeller))
    fig.canvas.mpl_connect('key_release_event',
                           lambda event: onrelease(event, labeller))
