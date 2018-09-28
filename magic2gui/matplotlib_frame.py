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
from tkinter.messagebox import askokcancel


class MFToolbar(NavigationToolbar2Tk):
    toolitems = list(NavigationToolbar2Tk.toolitems)
    # Delete the button for adjusting subplots, it was not useful in this
    # particular usecase, and could break things if used unwisely
    del toolitems[6]

    # Override the _update_view function so that it doesn't try setting
    # the plots position. It mostly failed to do that, and we're not planning
    # to change that posoition either way.
    # This function is mostly copied over from matplotlib's source
    def _update_view(self):
        # Update the viewlim and position from the view and
        # position stack for each axes.
        nav_info = self._nav_stack()
        if nav_info is None:
            return
        # Retrieve all items at once to avoid any risk of GC deleting an Axes
        # while in the middle of the loop below.
        items = list(nav_info.items())
        for ax, (view, (pos_orig, pos_active)) in items:
            ax._set_view(view)
            # There would normally be some view changing settings here...
        self.canvas.draw_idle()

    def save_figure(self, *args):
        if askokcancel("Using matplotlib's figure saving", "Please note that this will use matplotlib's built-in figure saving mechanism, which doesn't allow resolution setting. You may want to use 'File->Save the graph as an image', which allows you to set the resolution when exporting the graph presented in the main window."):
            NavigationToolbar2Tk.save_figure(self, *args)


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
            self.toolbar = MFToolbar(self.canvas, self)
            self.toolbar.update()
        # Pack the canvas in the Frame
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.canvas._tkcanvas.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)
        # Create a placeholder object for an animation
        self.ani = None
        # Bind keyboard shortcuts
        if bind_keys:
            # Delete default keyboard shortcuts that we will be using elsewhere
            rcParams['keymap.back'] = ['left']
            rcParams['keymap.save'] = ['ctrl+s']

            def on_key_press(event):
                # The default keypress handler
                key_press_handler(event, self.canvas, self.toolbar)
                # Grid handling (animation blit cache needs to cleaned
                # when grid shown)
                if event.key == 'g' and self.ani is not None:
                    self.ani._blit_cache.clear()
                # Keyboard navigation
                elif event.key == 'x':
                    # Zoom in
                    ylim = self.ax.get_ylim()
                    xlim = self.ax.get_xlim()
                    diffy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
                    diffx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                    self.ax.set_ylim([ylim[0]+0.1*diffy, ylim[1]-0.1*diffy])
                    self.ax.set_xlim([xlim[0]+0.1*diffx, xlim[1]-0.1*diffx])
                    self.fig.canvas.draw()
                    self.push_current()
                elif event.key == 'z':
                    # Zoom out
                    ylim = self.ax.get_ylim()
                    xlim = self.ax.get_xlim()
                    diffy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
                    diffx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                    self.ax.set_ylim([ylim[0]-0.1*diffy, ylim[1]+0.1*diffy])
                    self.ax.set_xlim([xlim[0]-0.1*diffx, xlim[1]+0.1*diffx])
                    self.fig.canvas.draw()
                    self.push_current()
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
                        self.push_current()
            self.canvas.mpl_connect("key_press_event", on_key_press)
        # Set focus back to canvas after clicking it
        self.canvas.mpl_connect('button_press_event',
                                lambda event: self.canvas._tkcanvas.focus_set())

    # Clear the view history stack...
    def clear_nav_stack(self):
        self.toolbar._nav_stack.clear()
        # ...and push the current view onto it
        self.push_current()

    # Push the current view onto the view history stack
    def push_current(self):
        self.toolbar.push_current()
        self.toolbar.set_history_buttons()
