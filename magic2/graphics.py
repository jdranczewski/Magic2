import numpy as np

def render_fringes(fringes, canvas, width=1):
    for fringe in fringes.list:
        for point in fringe.points:
            colour = 1
            for x in range(-width+1,width):
                for y in range(-width+1,width):
                    try:
                        canvas[point[0]+y, point[1]+x] = colour
                    except:
                        pass
