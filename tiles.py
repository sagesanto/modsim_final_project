from abc import ABC, abstractproperty, abstractmethod
import numpy as np
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D
import matplotlib.path as mpath
import matplotlib.patches as patches


class Tile(ABC):
    def __init__(self):
        self.index = None
    
    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y

    @abstractmethod
    def move_in(self,car):
        pass

    def set_index(self,index):
        self.index = index 
    
    @abstractmethod
    def marker(self,scale):
        pass

    @abstractproperty
    def occupied(self) -> bool:
        pass

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


class RoadMarker(mpath.Path):
    def __init__(self, p_directions, scale=1.0):
        vertices = []
        codes = []

        for i, p in enumerate(p_directions[:-1]):
            angle = 360 - i * 45
            if p:
                line_path = mpath.Path([[0, 0], [0, 1]], [mpath.Path.MOVETO, mpath.Path.LINETO])
                t = Affine2D().scale(p * 5 * scale).translate(0, 5 * scale).rotate_deg(angle)
                verts = t.transform(line_path.vertices)
                vertices.append(verts[0])
                codes.append(mpath.Path.MOVETO)
                vertices.extend(verts)
                codes.extend(line_path.codes)

        if p_directions[-1]:  # this is the chance to stay where we are
            dot_path = mpath.Path.unit_circle()
            t = Affine2D().scale(p_directions[-1] * 10 * scale)
            vertices.extend(t.transform(dot_path.vertices))
            codes.extend(dot_path.codes)
        
        self.marker = mpath.Path(vertices, codes)

        super().__init__(self.marker.vertices, self.marker.codes,closed=False)


class Road(Tile):
    def __init__(self,x:int,y:int,p_directions:np.ndarray):
        super().__init__()
        assert(len(p_directions)==9)
        assert(np.sum(p_directions)==1)
        self._x = x
        self._y = y
        self._directions =  np.array(p_directions,copy=True)
        self.p_directions = np.array(p_directions,copy=True)
        self.car = None
        self.neighbors = []
    
    @property
    def occupied(self) -> bool:
        return self.car is not None
    
    def move_in(self,car):
        if self.car is not None:
            raise ValueError("Cannot move car into this cell! It already has one!")
        self.car = car
    
    def marker(self, scale=1.0):
        return MarkerStyle(RoadMarker(self.p_directions, scale=scale))

    def plot(self,ax,**kwargs):
        ax.plot(self.x,self.y,marker=self.marker(1),markersize=50,**kwargs)
    
    def __repr__(self):
        return f"Road({self.x},{self.y},occupied={self.occupied})"


class Exit(Tile):
    def __init__(self,x:int,y:int) -> None:
        super().__init__()
        self._x = x
        self._y = y
        self.index = None
    
    def move_in(self,car):
        del(car)  # this feels like it will cause problems
    
    @property
    def occupied(self):
        return False
        