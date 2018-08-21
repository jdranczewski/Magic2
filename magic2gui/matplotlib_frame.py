# The GraphFrame class implements a matplotlib graph in an easy to use way.
# It inherits from tkinter's Frame and thus behaves like any other widget,
# but it also exposes a single subplot (self.subplot) which can be used
# like any other subplot in normal matplotlib Python code. A convenient
# toolbar can also be attached to the graph.
# init arguments are the parent frame, the figure's size, its dpi, a boolean
# variable that allows for simple binding of matplotlib's default key bindings,
# and a boolean variable that determines whether to show a toolbar.

import tkinter as Tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2TkAgg)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib import rcParams


class GraphFrame(Tk.Frame):
    def __init__(self, parent, figsize=(5, 4), dpi=100,
                 bind_keys=False, show_toolbar=False):
        # Cal the init function of tkinter's Frame
        Tk.Frame.__init__(self, parent)
        # Create a matplotlib Figure
        self.fig = Figure(figsize=figsize, dpi=dpi)
        self.fig.set_tight_layout(True)
        # Create a matplotlib subplot
        self.ax = self.fig.add_subplot(111)
        # Create and draw a canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        # Add a toolbar if needed
        if show_toolbar:
            toolbar = NavigationToolbar2TkAgg(self.canvas, self)
            toolbar.update()
        # Pack the canvas in the Frame
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.canvas._tkcanvas.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)
        # Bind keyboard shortcuts
        if bind_keys:
            rcParams['keymap.back'] = ['left', 'c']
            rcParams['keymap.save'] = ['ctrl+s']
            def on_key_press(event):
                key_press_handler(event, self.canvas, toolbar)
                # Keyboard navigation
                if event.key == 'x':
                    ylim = self.ax.get_ylim()
                    xlim = self.ax.get_xlim()
                    diffy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
                    diffx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                    self.ax.set_ylim([ylim[0]+0.1*diffy, ylim[1]-0.1*diffy])
                    self.ax.set_xlim([xlim[0]+0.1*diffx, xlim[1]-0.1*diffx])
                    self.fig.canvas.draw()
                elif event.key == 'z':
                    print("Doi")
                    ylim = self.ax.get_ylim()
                    xlim = self.ax.get_xlim()
                    diffy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
                    diffx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                    self.ax.set_ylim([ylim[0]-0.1*diffy, ylim[1]+0.1*diffy])
                    self.ax.set_xlim([xlim[0]-0.1*diffx, xlim[1]+0.1*diffx])
                    self.fig.canvas.draw()
                else:
                    dx = 0
                    dy = 0
                    if event.key == 'w':
                        dy = 1
                    elif event.key == 'a':
                        dx = -1
                    elif event.key == 's':
                        dy = -1
                    elif event.key == 'd':
                        dx = 1
                    if dx != 0 or dy != 0:
                        ylim = self.ax.get_ylim()
                        xlim = self.ax.get_xlim()
                        diffy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
                        diffx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                        self.ax.set_ylim([ylim[0]+0.3*diffy*dy, ylim[1]+0.3*diffy*dy])
                        self.ax.set_xlim([xlim[0]+0.3*diffx*dx, xlim[1]+0.3*diffx*dx])
                        self.fig.canvas.draw()
            self.canvas.mpl_connect("key_press_event", on_key_press)
        # Set focus back to canvas after clicking it
        self.canvas.mpl_connect('button_press_event',
                                lambda event: self.canvas._tkcanvas.focus_set())

    # Redraw the canvas to show new data (if updated)
    def draw(self):
        self.canvas.draw()
