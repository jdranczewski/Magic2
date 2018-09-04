import tkinter as Tk
import tkinter.ttk as ttk
from matplotlib.animation import FuncAnimation
import scipy as sp
from skimage.measure import profile_line

import magic2gui.matplotlib_frame as m2mframe


# A class for working with layouts
class Lineout():
    # This creates a lineout based on coordinates passed as 'line'
    def __init__(self, line, options):
        # Save a reference to the options object
        self.options = options
        # Save the mode the lineout was created in
        self.mode = options.mode

        # Save the coordinates of the line
        self.line = line.copy()
        # The coordinates have to be in pixels, not in mm
        if options.mode == "density_graph":
            self.line *= options.resolution
        # Draw the line on the graph, using the initially supplied
        # coordinates (could be in mm)
        self.line_plot, = options.ax.plot(line[:, 1], line[:, 0])
        options.fig.canvas.draw()

        # Create a window for the lineout
        window = self.window = Tk.Toplevel()
        # Transient means modal in this case - doesn't show up in the
        # taskbar, cannot be minimised, etc.
        # window.transient(options.root)
        # Set the focus to the new window
        window.focus_set()
        # Place the window close to the root one
        window.geometry("+%d+%d" % (options.root.winfo_rootx()+50,
                                    options.root.winfo_rooty()+50))
        # Attach an event listener for when the window's closed
        window.protocol("WM_DELETE_WINDOW", self.remove)

        # Create the options
        b = ttk.Button(window, text="test", command=lambda: options.show_var.set("background_fringes"))
        b.pack()

        # Calculate the profile
        self.profile = profile_line(sp.ma.filled(options.imshow.get_array().astype(float), fill_value=sp.nan), self.line[0], self.line[1])

        # Create the matplotlib frame
        self.mframe = m2mframe.GraphFrame(window, bind_keys=True, show_toolbar=True)
        # Create an x axis, with the units depending on the mode
        if options.mode == "density_graph":
            xspace = sp.linspace(0, len(self.profile)/options.resolution, len(self.profile))
        else:
            xspace = sp.linspace(0, len(self.profile), len(self.profile))
        # Plot the lineout
        self.mframe.ax.plot(xspace, self.profile)
        # Pack the frame, filling all available space
        self.mframe.pack(fill=Tk.BOTH, expand=1)

    # This function can be used to redraw the Lineout. Used in the
    # set_mode callback
    def update(self):
        # Check if the line will require to be scaled (self.line is in pixels)
        if self.options.mode == "density_graph":
            scale = self.options.resolution
        else:
            scale = 1
        # If we are in the mode in which the lineout was created, draw
        # a solid line. Otherwise, draw a dashed one
        if self.options.mode == self.mode:
            self.line_plot, = self.options.ax.plot(self.line[:, 1]/scale, self.line[:, 0]/scale)
        else:
            self.line_plot, = self.options.ax.plot(self.line[:, 1]/scale, self.line[:, 0]/scale, "--")

    # Delete the lineout when the associated window is closed
    def remove(self):
        # Remove the line from the graph
        self.line_plot.remove()
        self.options.fig.canvas.draw()
        # Remove this lineout from the list of active ones
        self.options.lineouts.remove(self)
        # Set the focus back to the main window
        self.options.root.focus_set()
        # Destroy the lineout's window
        self.window.destroy()


# //Event handlers for the lineout creation process//
def lineout_onclick(event, line_plot, options, binds, ani):
    line = line_plot.get_data()
    # Create the first point of the line
    if len(line[0]) == 0 and event.inaxes == options.ax:
        line_plot.set_data((event.xdata,), (event.ydata,))
    # The second point is added by the onmove function. If there's two points,
    # confirm the lineout's creation
    elif len(line) == 2 and event.inaxes == options.ax:
        # Convert the data into the format of [[y0, x0],
        #                                      [y1, x1]]
        line = sp.array(line).transpose()[:, ::-1]
        stop_lineout(options)
        # Create a Lineout object
        lineout = Lineout(line, options)
        # Add the object ot the list of active lineouts
        options.lineouts.append(lineout)


def lineout_onmove(event, line_plot, ax):
    line = line_plot.get_data()
    # If the line has a point on it...
    if len(line[0]) and event.inaxes == ax:
        # ...add the current mouse position as the second point
        line_plot.set_data([line[0][0], event.xdata], [line[1][0], event.ydata])


# Esc key cancels layout creation
def lineout_onpress(event, line_plot, options, binds, ani):
    if event.key == "escape":
        stop_lineout(options)


# This tells FuncAnimation which objects it needs to redraw
def ani_update(i, line_plot):
    return line_plot,


# This function is used to start the layout creation process
def create_lineout(options):
    # If a lineout is currently being drawn, stop it
    if options.lineout_meta is not None:
        stop_lineout(options)
    # Change the cursor to a crosshair
    options.root.config(cursor="crosshair")
    # Plot an empty line
    line_plot, = options.ax.plot([], [], "--", color="tab:orange", animated=True)
    # Create and start the animation. blit=True speeds it up significantly
    ani = FuncAnimation(options.fig, ani_update, interval=100,
                        fargs=(line_plot,), blit=True)
    options.fig.canvas.draw()
    # Bind the event handlers
    binds = [None, None, None]
    binds[0] = options.fig.canvas.mpl_connect('button_press_event',
        lambda event: lineout_onclick(event, line_plot, options, binds, ani))
    binds[1] = options.fig.canvas.mpl_connect('motion_notify_event',
        lambda event: lineout_onmove(event, line_plot, options.ax))
    binds[2] = options.fig.canvas.mpl_connect('key_press_event',
        lambda event: lineout_onpress(event, line_plot, options, binds, ani))
    # Save the data about the current lineout creation process. This will
    # be used to stop the process, especially from the set_mode callback
    options.lineout_meta = [binds, ani, line_plot]


# Stop the process of creating the layout
def stop_lineout(options):
    # Unbind the event listeners
    for bind in options.lineout_meta[0]:
        options.fig.canvas.mpl_disconnect(bind)
    # Change the cursor back
    options.root.config(cursor="")
    # Stop the animation
    options.lineout_meta[1]._stop()
    # Remove the line_plot
    options.lineout_meta[2].remove()
    options.fig.canvas.draw()
    # Clear the variable
    options.lineout_meta = None
