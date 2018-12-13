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


# This ingerits from Tk.Frame, so behaves like a widget
class StatusBar(Tk.Frame):
    def __init__(self, master):
        Tk.Frame.__init__(self, master, bd=2, relief=Tk.SUNKEN)
        self.master = master
        # Create and pack a label displaying the project's name
        self.name_label = Tk.Label(self, text="")
        self.name_label.pack(side=Tk.LEFT)
        # Create and pack a progress bar
        self.pb = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.pb.pack(side=Tk.RIGHT)
        self.pb['value'] = 0
        # Create and pack a label with some default text
        self.label = Tk.Label(self, text="Use the file menu to open a traced interferogram", anchor=Tk.E)
        self.label.pack(side=Tk.RIGHT, fill='both')

    # Update the label and the progress bar
    def set(self, text, value):
        # Indeterminate should not be used often, as it does not refresh
        # when calculations are happenning
        if value == -1:
            self.pb['mode'] = 'indeterminate'
            self.pb.start(10)
        else:
            self.pb['mode'] = 'determinate'
            self.pb.stop()
            self.pb['value'] = value
        self.label['text'] = text
        # Update everything!
        self.pb.update_idletasks()
        self.label.update_idletasks()
        self.update_idletasks()
        self.master.update()

    # Update the name label
    def set_name_label(self, text):
        self.name_label['text'] = text
        self.name_label.update_idletasks()
