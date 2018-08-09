# This file contains functionality related to dealing with fringes


class Fringes():
    def __init__(self):
        # Max is the maximum phase index
        self.max = 0
        # List is a list of pointers to particular fringes
        self.list = []

class Fringe():
    def __init__(self, points):
        # List of points in the fringe
        self.points = points
        # Phase is an integer, going from 0 up
        self.phase = 0
