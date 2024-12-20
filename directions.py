# p_directions goes clockwise:
    #[ p(N)    0
    #  p(NE)   1
    #  p(E)    2
    #  p(SE)   3
    #  p(S)    4
    #  p(SW)   5
    #  p(W)    6
    #  p(NW)   7
    #  p(stay) 8 ]
# must sum to 1
import numpy as np
NORTH = np.array([1.0,0,0,0,0,0,0,0,0])
NORTHEAST = np.array([0,1.0,0,0,0,0,0,0,0])
EAST = np.array([0,0,1.0,0,0,0,0,0,0])
SOUTHEAST = np.array([0,0,0,1.0,0,0,0,0,0])
SOUTH = np.array([0,0,0,0,1.0,0,0,0,0])
SOUTHWEST = np.array([0,0,0,0,0,1.0,0,0,0])
WEST = np.array([0,0,0,0,0,0,1.0,0,0])
NORTHWEST = np.array([0,0,0,0,0,0,0,1.0,0])
STAY = np.array([0,0,0,0,0,0,0,0,1.0])
NORTH_NORTHEAST = 0.75*NORTH + 0.25*NORTHEAST
NORTH_NORTHWEST = 0.75*NORTH + 0.25*NORTHWEST
NORTH_NORTHEAST_NORTHWEST = 0.75*NORTH + 0.125*NORTHEAST + 0.125*NORTHWEST
EAST_NORTHEAST = 0.75*EAST + 0.25*NORTHEAST
EAST_SOUTHEAST = 0.75*EAST + 0.25*SOUTHEAST
EAST_NORTHEAST_SOUTHEAST = 0.75*EAST + 0.125*NORTHEAST + 0.125*SOUTHEAST
SOUTH_SOUTHEAST = 0.75*SOUTH + 0.25*SOUTHEAST
SOUTH_SOUTHWEST = 0.75*SOUTH + 0.25*SOUTHWEST
SOUTH_SOUTHEAST_SOUTHWEST = 0.75*SOUTH + 0.125*SOUTHEAST + 0.125*SOUTHWEST

directions = [NORTH, NORTHEAST, EAST, SOUTHEAST, SOUTH, SOUTHWEST, WEST, NORTHWEST, STAY,
              NORTH_NORTHEAST, NORTH_NORTHWEST, NORTH_NORTHEAST_NORTHWEST, EAST_NORTHEAST, EAST_SOUTHEAST, EAST_NORTHEAST_SOUTHEAST,
              SOUTH_SOUTHEAST, SOUTH_SOUTHWEST, SOUTH_SOUTHEAST_SOUTHWEST]
direction_names = ["NORTH", "NORTHEAST", "EAST", "SOUTHEAST", "SOUTH", "SOUTHWEST", "WEST", "NORTHWEST", "STAY","NORTH-NORTHEAST", "NORTH-NORTHWEST", "NORTH-NORTHEAST-NORTHWEST", "EAST-NORTHEAST", "EAST-SOUTHEAST", "EAST-NORTHEAST-SOUTHEAST","SOUTH-SOUTHEAST", "SOUTH-SOUTHWEST", "SOUTH-SOUTHEAST-SOUTHWEST"]

N = NORTH
NE = NORTHEAST
E = EAST
SE = SOUTHEAST
S = SOUTH
SW = SOUTHWEST
W = WEST
NW = NORTHWEST