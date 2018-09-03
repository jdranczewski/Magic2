import tkinter as Tk
import tkinter.ttk as ttk
from matplotlib.animation import FuncAnimation
import scipy as sp
from skimage.measure import profile_line

import magic2gui.matplotlib_frame as m2mframe


class Lineout():
    def __init__(self, line, options):
        self.options = options
        self.line = line
        self.line_plot, = options.ax.plot(line[:, 1], line[:, 0])
        options.fig.canvas.draw()

        window = self.window = Tk.Toplevel()
        window.transient(options.root)
        # top.grab_set()
        window.focus_set()
        window.geometry("+%d+%d" % (options.root.winfo_rootx()+50,
                                    options.root.winfo_rooty()+50))
        window.protocol("WM_DELETE_WINDOW", self.remove)
        b = ttk.Button(window, text="test", command=lambda: options.show_var.set("background_fringes"))
        b.pack()

        self.profile = profile_line(sp.ma.filled(options.imshow.get_array().astype(float), fill_value=sp.nan), line[0], line[1])
        self.mframe = m2mframe.GraphFrame(window, bind_keys=True, show_toolbar=True)
        self.mframe.ax.plot(self.profile)
        self.mframe.pack()

    def remove(self):
        self.line_plot.remove()
        self.options.root.focus_set()
        self.window.destroy()
        self.options.fig.canvas.draw()


def lineout_onclick(event, line_plot, options, binds, ani):
    line = line_plot.get_data()
    if len(line[0]) == 0:
        line_plot.set_data((event.xdata,), (event.ydata,))
    elif len(line) == 2:
        line = sp.array(line).transpose()[:, ::-1]
        stop_lineout(options)
        lineout = Lineout(line, options)


def lineout_onmove(event, line_plot, ax):
    line = line_plot.get_data()
    if len(line[0]) and event.inaxes == ax:
        line_plot.set_data([line[0][0], event.xdata], [line[1][0], event.ydata])


def lineout_onpress(event, line_plot, options, binds, ani):
    if event.key == "escape":
        stop_lineout(options)


def ani_update(i, line_plot):
    return line_plot,

# Set centre of the plasma density map
def create_lineout(options):
    options.root.config(cursor="crosshair")
    line = []
    line_plot, = options.ax.plot([], [], "--", color="tab:orange", animated=True)
    ani = FuncAnimation(options.fig, ani_update, interval=100,
                        fargs=(line_plot,), blit=True)
    options.fig.canvas.draw()
    binds = [None, None, None]
    binds[0] = options.fig.canvas.mpl_connect('button_press_event',
        lambda event: lineout_onclick(event, line_plot, options, binds, ani))
    binds[1] = options.fig.canvas.mpl_connect('motion_notify_event',
        lambda event: lineout_onmove(event, line_plot, options.ax))
    binds[2] = options.fig.canvas.mpl_connect('key_press_event',
        lambda event: lineout_onpress(event, line_plot, options, binds, ani))
    options.lineout_meta = [binds, ani, line_plot]


def stop_lineout(options):
    for bind in options.lineout_meta[0]:
        options.fig.canvas.mpl_disconnect(bind)
    options.root.config(cursor="")
    options.lineout_meta[1]._stop()
    options.lineout_meta[2].remove()
    options.fig.canvas.draw()
    options.lineout_meta = None
