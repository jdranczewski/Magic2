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

import tkinter as Tk
import tkinter.ttk as ttk
import tkinter.filedialog as fd
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Polygon
import scipy as sp
import ctypes
from skimage.measure import profile_line

import magic2gui.matplotlib_frame as m2mframe


# A class for working with layouts
class Lineout():
    # This creates a lineout based on coordinates passed as 'line'.
    # 'redoing' is a Lineout object passed if we're recalculating
    # an existing lineout in a different mode
    def __init__(self, line, options, redoing=None):
        # Save a reference to the options object
        self.options = options
        # Save the mode the lineout was created in
        self.mode = options.mode
        # Set the colour (blue is default) and width of the lineout
        if redoing is not None:
            self.colour = redoing.colour
            self.width = redoing.width
        else:
            self.colour = 'tab:blue'
            self.width = 1

        # Save the coordinates of the line
        self.line = line.copy()
        # The coordinates have to be in pixels, not in mm
        if options.mode == "density_graph" and redoing is None:
            self.line *= options.resolution
            self.line += options.centre
        # Check if the line will require to be scaled or moved while drawing
        # (self.line is always pixels and relative to the left top corner)
        if self.options.mode == "density_graph":
            scale = self.options.resolution
            offset = self.options.centre
        else:
            scale = 1
            offset = [0, 0]
        # Draw the line on the graph
        self.line_plot, = options.ax.plot((self.line[:, 1]-offset[1])/scale,
                                          (self.line[:, 0]-offset[0])/scale,
                                          color=self.colour)

        # Draw the rectangle
        patch = Polygon(self.get_verts(), color=self.colour, linewidth=0,
                        alpha=0.3)
        self.rect = options.ax.add_patch(patch)
        self.main_canvas_draw()

        # Create a window for the lineout
        window = self.window = Tk.Toplevel()
        self.transient = False
        window.wm_title(" ".join(options.mode.split("_")) + " lineout - " + options.namecore)
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
        window.focus_set()
        # Place the window close to the root one
        if redoing is not None:
            window.geometry("+%d+%d" % (redoing.window.winfo_rootx(),
                                        redoing.window.winfo_rooty()))
        else:
            window.geometry("+%d+%d" % (options.root.winfo_rootx()+50,
                                        options.root.winfo_rooty()+50))
        # Attach an event listener for when the window's closed
        window.protocol("WM_DELETE_WINDOW", self.remove)

        # Create the options
        oframe = Tk.Frame(window)
        oframe.pack(side=Tk.BOTTOM, fill=Tk.BOTH)
        for i in range(3):
            oframe.grid_columnconfigure(i, weight=1)
        b = ttk.Button(oframe, text="Export lineout", command=self.export)
        b.grid(sticky=("N", "S", "E", "W"))
        b = ttk.Button(oframe, text="Redraw in current mode", command=self.redo)
        b.grid(row=0, column=1, sticky=("N", "S", "E", "W"))
        self.pinvar = Tk.StringVar()
        self.pinvar.set("Pin this window")
        b = ttk.Button(oframe, textvariable=self.pinvar, command=self.un_pin)
        b.grid(row=0, column=2, sticky=("N", "S", "E", "W"))
        wframe = Tk.Frame(oframe)
        wframe.grid(row=1, column=0, sticky=Tk.W)
        ttk.Label(wframe, text="Width (px):").pack(side=Tk.LEFT)
        self.width_box = Tk.Spinbox(wframe, from_=1, to=1024, increment=1,
                                    width=4, command=self.update_width)
        self.width_box.bind("<Return>", self.update_width)
        if redoing is not None:
            self.width_box.delete(0, Tk.END)
            self.width_box.insert(Tk.END, redoing.width)
        self.width_box.pack(side=Tk.LEFT)
        self.showboxvar = Tk.BooleanVar()
        self.showboxvar.set(True)
        self.sb = ttk.Checkbutton(oframe, text="Show bounding box",
                                  variable=self.showboxvar,
                                  command=self.update_vis)
        self.sb.grid(row=1, column=1)
        cframe = Tk.Frame(oframe)
        cframe.grid(row=1, column=2, sticky=Tk.E)
        ttk.Label(cframe, text="Colour:").pack(side=Tk.LEFT)
        self.colourvar = Tk.StringVar()
        # A list of the basic matplotlib colours
        choice = ('tab:blue', 'tab:orange', 'tab:green', 'tab:red',
                  'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
                  'tab:olive', 'tab:cyan')
        # The star (*) unpacks the above tuple, as ttk.OptionMenu takes options
        # as just a lot of arguments
        self.colour_option = ttk.OptionMenu(cframe, self.colourvar, self.colour,
                                            *choice, command=self.update_colour)
        self.colour_option.pack(side=Tk.LEFT)

        # Calculate the profile
        self.profile = profile_line(sp.ma.filled(options.imshow.get_array().astype(float), fill_value=sp.nan), self.line[0], self.line[1], linewidth=self.width)

        # Create the matplotlib frame
        self.mframe = m2mframe.GraphFrame(window, bind_keys=True,
                                          show_toolbar=True)
        # Create an x axis, with the units depending on the mode
        if options.mode == "density_graph":
            self.xspace = sp.linspace(0, len(self.profile)/options.resolution,
                                      len(self.profile))
            self.mframe.ax.set_xlabel("Distance / $mm$")
            self.mframe.ax.set_ylabel("Electron density / $cm^{-3}$")
        else:
            self.xspace = sp.linspace(0, len(self.profile), len(self.profile))
            self.mframe.ax.set_xlabel("Distance / $px$")
            self.mframe.ax.set_ylabel("Fringes")
        # Plot the lineout
        self.mframe.ax.plot(self.xspace, self.profile, color=self.colour)
        # Set the limits so that the entire length of the lineout is shown
        self.mframe.ax.set_xlim([0, sp.amax(self.xspace)])
        # Push the current view onto the view history stack
        self.mframe.push_current()
        # Pack the frame, filling all available space
        self.mframe.pack(fill=Tk.BOTH, expand=1)
        # Give the focus to the graph
        self.mframe.canvas._tkcanvas.focus_set()

    # This function calculates the vertices of a rectangle of
    # a given width along the lineout
    def get_verts(self):
        if self.options.mode == "density_graph":
            scale = self.options.resolution
            offset = self.options.centre
        else:
            scale = 1
            offset = [0, 0]
        line = (self.line - offset)/scale
        dy = line[1, 0] - line[0, 0]
        dx = line[1, 1] - line[0, 1]
        wx = self.width/2/scale * sp.sin(sp.arctan2(dy, dx))
        wy = -self.width/2/scale * sp.cos(sp.arctan2(dy, dx))
        verts = sp.array([
            [line[0, 1]-wx, line[0, 0]-wy],
            [line[0, 1]+wx, line[0, 0]+wy],
            [line[1, 1]+wx, line[1, 0]+wy],
            [line[1, 1]-wx, line[1, 0]-wy]
        ])
        return verts

    # This function can be used to redraw the Lineout. Used in the
    # set_mode callback
    def update(self):
        # Check if the line will require to be scaled (self.line is in pixels)
        if self.options.mode == "density_graph":
            scale = self.options.resolution
            offset = self.options.centre
        else:
            scale = 1
            offset = [0, 0]
        # If we are in the mode in which the lineout was created, draw
        # a solid line. Otherwise, draw a dashed one
        if self.options.mode == self.mode:
            self.line_plot, = self.options.ax.plot((self.line[:, 1]-offset[1])/scale,
                                                   (self.line[:, 0]-offset[0])/scale,
                                                   color=self.colour)
            # Draw the rectangle
            patch = Polygon(self.get_verts(), color=self.colour,
                            linewidth=0, alpha=0.3)
            self.rect = self.options.ax.add_patch(patch)
            self.update_vis(draw=False)
            # Make the width controls active
            self.width_box.config(state=Tk.NORMAL)
            self.sb.config(state=Tk.NORMAL)
        else:
            self.line_plot, = self.options.ax.plot((self.line[:, 1]-offset[1])/scale,
                                                   (self.line[:, 0]-offset[0])/scale, "--",
                                                   color=self.colour,
                                                   alpha=0.7)
            self.rect = None
            # Disable the width controls
            self.width_box.config(state=Tk.DISABLED)
            self.sb.config(state=Tk.DISABLED)

    # Delete the lineout when the associated window is closed
    def remove(self):
        # Remove the line from the graph
        self.line_plot.remove()
        # Remove the rectangle if exists
        if self.rect is not None:
            self.rect.remove()
        self.main_canvas_draw()
        # Remove this lineout from the list of active ones
        self.options.lineouts.remove(self)
        # Set the focus back to the main window
        self.options.root.focus_set()
        # Destroy the lineout's window
        self.window.destroy()

    # Export the lineout data
    def export(self):
        filename = fd.asksaveasfilename(filetypes=[(".csv file", "*.csv"),
                                                   ("All files", "*")],
                                        defaultextension=".csv",
                                        initialfile=self.options.namecore)
        # Give focus back to the lineout window
        self.window.focus_set()
        # Give the focus to the graph
        self.mframe.canvas._tkcanvas.focus_set()
        if filename != '':
            # Add appropriate units to the header
            if self.mode.split("_")[0] == "density":
                header = "distance (mm),\tplasma density (cm^-3)"
                scale = self.options.resolution
                units = "mm"
            else:
                header = "distance (px),\tfringes"
                scale = 1
                units = "px"
            # Add some metadata to the header
            header = "start: {}{}\nend: {}{}\nmode: {}\n".format(
                self.line[0, ::-1]/scale, units,
                self.line[1, ::-1]/scale, units,
                self.mode
            ) + header
            # Save the data under the given filename
            sp.savetxt(filename,
                       sp.vstack((self.xspace, self.profile)).transpose(),
                       header=header)

    # Redraw and recalculate the lineout in the current mode
    def redo(self):
        # Create a Lineout object
        lineout = Lineout(self.line, self.options, redoing=self)
        # Add the object ot the list of active lineouts
        self.options.lineouts.append(lineout)
        # Remove this object
        self.remove()

    # Pin/Unpin the window:
    def un_pin(self):
        # Transient means modal in this case - doesn't show up in the
        # taskbar, cannot be minimised, etc.
        if self.transient:
            self.window.transient("")
            self.pinvar.set("Pin this window")
        else:
            self.window.transient(self.options.root)
            self.pinvar.set("Unpin this window")
        self.transient = not self.transient
        # Give the focus to the graph
        self.mframe.canvas._tkcanvas.focus_set()

    # Update the Lineout's width
    def update_width(self, *args):
        self.width = float(self.width_box.get())
        self.profile = profile_line(sp.ma.filled(self.options.imshow.get_array().astype(float), fill_value=sp.nan), self.line[0], self.line[1], linewidth=self.width)
        self.mframe.ax.lines[0].set_data(self.xspace, self.profile)
        # Redraw the graph in lineout's window
        self.mframe.fig.canvas.draw()
        # Change the verices of the rectangle in the main window
        self.rect.set_xy(self.get_verts())
        self.main_canvas_draw()
        # Give the focus to the graph
        self.mframe.canvas._tkcanvas.focus_set()

    # Show or hide the bounding box
    def update_vis(self, draw=True):
        if self.rect is not None:
            self.rect.set_visible(self.showboxvar.get())
            if draw:
                self.main_canvas_draw()
        # Give the focus to the graph
        self.mframe.canvas._tkcanvas.focus_set()

    # Update the lineout's colour and draw the necessary lines
    def update_colour(self, *args):
        self.colour = self.colourvar.get()
        self.line_plot.set_color(self.colour)
        if self.rect is not None:
            self.rect.set_color(self.colour)
        self.mframe.ax.lines[0].set_color(self.colour)
        self.mframe.fig.canvas.draw()
        self.main_canvas_draw()

    # A function that draws the canvas of the main figure, but also clears
    # the blitting cache of any labelling animation currently happening
    def main_canvas_draw(self):
        if self.options.labeller is not None:
            self.options.labeller.ani._blit_cache.clear()
        self.options.fig.canvas.draw()


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


# This tells FuncAnimation which objects it needs to redraw.
# It also clears the animation cache if it notices the graph limits
# have changed
def ani_update(i, line_plot, options, prev_lim):
    if prev_lim != [options.ax.get_xlim(), options.ax.get_ylim()]:
        # If the limits change, do a redraw. This is slooow, but actually works
        # (the slight overhead with scrolling is worth it, as we get
        # significant improvements when drawing lines)
        prev_lim[0], prev_lim[1] = options.ax.get_xlim(), options.ax.get_ylim()
        options.lineout_meta[1]._blit_cache.clear()
        options.fig.canvas.draw()
    return line_plot,


# This function is used to start the layout creation process
def create_lineout(options):
    # If a lineout is currently being drawn, stop it
    if options.lineout_meta is not None:
        stop_lineout(options)
    # Change the cursor to a crosshair
    options.mframe.config(cursor="crosshair")
    # Plot an empty line
    line_plot, = options.ax.plot([], [], "--", color="tab:orange", animated=True)
    # Create and start the animation. blit=True speeds it up significantly
    prev_lim = [options.ax.get_xlim(), options.ax.get_ylim()]
    ani = FuncAnimation(options.fig, ani_update, interval=100,
                        fargs=(line_plot, options, prev_lim), blit=True)
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
    options.mframe.config(cursor="")
    # Stop the animation
    options.lineout_meta[1]._stop()
    # Remove the line_plot
    options.lineout_meta[2].remove()
    options.fig.canvas.draw()
    # Clear the variable
    options.lineout_meta = None
