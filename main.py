import tkinter.filedialog

def main():
    filename = tkinter.filedialog.askopenfile()
    print(filename.name)


if __name__ == "__main__":
    main()
