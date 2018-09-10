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
