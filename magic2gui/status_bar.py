import tkinter as Tk
import tkinter.ttk as ttk

class StatusBar(Tk.Frame):
    def __init__(self, master):
        Tk.Frame.__init__(self, master, bd=2, relief=Tk.SUNKEN)
        self.master = master
        self.pb = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.pb.pack(side=Tk.RIGHT)
        self.pb['value'] = 0
        self.label = Tk.Label(self, text="Use the file menu to open a traced interferogram", anchor=Tk.E)
        self.label.pack(side=Tk.RIGHT, fill='both')

    def set(self, text, value):
        if value == -1:
            self.pb['mode'] = 'indeterminate'
            self.pb.start(10)
        else:
            self.pb['mode'] = 'determinate'
            self.pb.stop()
            self.pb['value'] = value
        self.label['text'] = text
        self.pb.update_idletasks()
        self.label.update_idletasks()
        self.update_idletasks()
        self.master.update()
