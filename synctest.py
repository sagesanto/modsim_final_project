import sys, os
from os.path import join, dirname, abspath
import matplotlib.pyplot as plt
from matplotlib.pyplot import Figure, Axes
import numpy as np
import networkx as nx
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable
from directions import *
from string import ascii_uppercase
plt.rcParams.update({
    "text.usetex": False,
    "ytick.minor.visible":False,
    "xtick.minor.visible":False,
    'xtick.direction': "in",
    'ytick.direction': "in"
})

outdir = "out"
os.makedirs(outdir,exist_ok=True)
def out(fname): return join(outdir,fname)
def savefig(plot_name): 
    plt.savefig(out(plot_name),bbox_inches="tight",dpi=250)
    
import pandas as pd
from numpy.linalg import matrix_power, eig

def arr_to_latex(M):
    return '$$\n' + r'\begin{bmatrix}' + '\n' + (r'\\' + '\n').join('&'.join(str(x) for x in row) for row in M) + '\n' + r'\end{bmatrix}' + '\n' +'$$'

def vec_to_latex(x,round=3):
    return '$$\n' + r'\begin{bmatrix}' + '\n' + (r' \\ ').join(str(np.round(v,round)) for v in x) + '\n' + r'\end{bmatrix}' + '\n' +'$$'

from car import Car
from tiles import Road, Exit, Onramp
from world import World
from traffic_signals import Stoplight


straight = [Onramp(0,0,E)]
for i in range(19):
    straight.append(Road(i+1,0,E))

straight[-1]=Exit(i,0,E)
w = World(tiles=straight,cars=[])
w.add_stoplight(Stoplight(w.tiles[3,0],direction=6,period=10))
w.add_stoplight(Stoplight(w.tiles[8,0],direction=6,period=10,offset=5))
# w.draw(markersize=10)
w.run(100,draw=False)