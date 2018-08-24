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
