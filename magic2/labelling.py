import numpy as np


class Labeller():
    def __init__(self):
        self.points = []
        self.control = False


def onclick(event, labeller, line_plot):
    if labeller.control and not event.dblclick:
        labeller.points.append([event.ydata, event.xdata])
        points = np.array(labeller.points)
        line_plot.set_data(points[:, 1], points[:, 0])
        line_plot.figure.canvas.draw()
    elif event.dblclick:
        pass


def onmove(event, labeller, line_plot):
    if len(labeller.points) and event.ydata:
        points = np.append(np.array(labeller.points), [[event.ydata, event.xdata]],0)
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
                           lambda event: onclick(event, labeller, line_plot))
    fig.canvas.mpl_connect('motion_notify_event',
                           lambda event: onmove(event, labeller, line_plot))
    fig.canvas.mpl_connect('key_press_event',
                           lambda event: onpress(event, labeller))
    fig.canvas.mpl_connect('key_release_event',
                           lambda event: onrelease(event, labeller))
