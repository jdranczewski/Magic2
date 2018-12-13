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

# Based on http://effbot.org/tkinterbook/tkinter-dialog-windows.htm

import tkinter as Tk
import tkinter.ttk as ttk


class Dialog(Tk.Toplevel):
    def __init__(self, parent, title=None, parent_mframe=None, pad=True):
        Tk.Toplevel.__init__(self, parent)
        # Store the parent's mframe - focus is returned to it after
        # the dialog closes
        self.parent_mframe = parent_mframe
        # Make the window not show up in the window manager
        self.transient(parent)
        # Set the title
        if title:
            self.title(title)
        self.parent = parent
        # Initiate self.result just in case
        self.result = None
        # Create the main frame to put elements into
        body = Tk.Frame(self)
        # Create the elements and get the initial focus element
        self.initial_focus = self.body(body)
        if pad:
            body.pack(padx=5, pady=5)
        else:
            body.pack(fill=Tk.BOTH, expand=1)
        # Create the buttons
        self.buttonbox()
        # Make the dialog modal
        self.grab_set()
        # Set the initial focus depending on whether self.body() returned sth
        if not self.initial_focus:
            self.initial_focus = self
        self.initial_focus.focus_set()
        # If dialog is closed, call cancel
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        # Position the window close to parent
        self.geometry("+{}+{}".format(parent.winfo_rootx()+50,
                                      parent.winfo_rooty()+50))
        # Set the icon
        try:
            self.iconbitmap("magic2.ico")
        except:
            pass
        # Make the main window wait
        self.wait_window(self)

    # Override to create body
    def body(self, master):
        pass

    # Create the buttons
    def buttonbox(self):
        box = Tk.Frame(self)
        w = ttk.Button(box, text="OK", width=10, command=self.ok,
                       default=Tk.ACTIVE)
        w.pack(side=Tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=Tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set()
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        if self.parent_mframe is not None:
            # Give the focus back to the graph
            self.parent_mframe.canvas._tkcanvas.focus_set()
        self.destroy()

    # Override to validate
    def validate(self):
        return 1

    # Override to apply
    def apply(self):
        pass
