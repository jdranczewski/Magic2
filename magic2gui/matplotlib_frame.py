# The GraphFrame class implements a matplotlib graph in an easy to use way.
# It inherits from tkinter's Frame and thus behaves like any other widget,
# but it also exposes a few things like .ax and .cax which can be used
# for plotting (like normal matplotlib subplots).
# init arguments are the parent frame, the figure's size, its dpi, a boolean
# variable that allows for simple binding of matplotlib's default key bindings,
# and a boolean variable that determines whether to show a toolbar.

import tkinter as Tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
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
        # Create a subplot for the colorbar and hide it.
        # The make_lens_locatable function allows us to attach this
        # subplot to the main subplot and makes the colorbar stick
        # to the main graph nicely
        divider = make_axes_locatable(self.ax)
        self.cax = divider.append_axes("right", size="5%", pad=0.05)
        self.cax.axis('off')
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
            # Delete default keyboard shortcuts that we will be using elsewhere
            rcParams['keymap.back'] = ['left']
            rcParams['keymap.save'] = ['ctrl+s']

            def on_key_press(event):
                # The default keypress handler
                key_press_handler(event, self.canvas, toolbar)
                # Keyboard navigation
                if event.key == 'x':
                    # Zoom in
                    ylim = self.ax.get_ylim()
                    xlim = self.ax.get_xlim()
                    diffy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
                    diffx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                    self.ax.set_ylim([ylim[0]+0.1*diffy, ylim[1]-0.1*diffy])
                    self.ax.set_xlim([xlim[0]+0.1*diffx, xlim[1]-0.1*diffx])
                    self.fig.canvas.draw()
                elif event.key == 'z':
                    # Zoom out
                    ylim = self.ax.get_ylim()
                    xlim = self.ax.get_xlim()
                    diffy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
                    diffx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                    self.ax.set_ylim([ylim[0]-0.1*diffy, ylim[1]+0.1*diffy])
                    self.ax.set_xlim([xlim[0]-0.1*diffx, xlim[1]+0.1*diffx])
                    self.fig.canvas.draw()
                else:
                    # Move
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
                # Our wasd navigation messes up the views stack matplotlib
                # normally uses, so we define our own home function,
                # accessible by pressing 'h'
                def new_home():
                    print("New home")
                    self.ax.autoscale()
                    self.fig.canvas.draw()
                toolbar.home = new_home
            self.canvas.mpl_connect("key_press_event", on_key_press)
        # Set focus back to canvas after clicking it
        self.canvas.mpl_connect('button_press_event',
                                lambda event: self.canvas._tkcanvas.focus_set())

    # Redraw the canvas to show new data (if updated)
    def draw(self):
        self.canvas.draw()
