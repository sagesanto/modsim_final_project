from abc import ABC, abstractproperty, abstractmethod
import numpy as np
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D
import matplotlib.path as mpath
import matplotlib.patches as patches

from car import Car 

rng = np.random.default_rng()

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

    @abstractmethod
    def move_out(self,car):
        pass

    def set_index(self,index):
        self.index = index 
    
    @abstractmethod
    def marker(self,scale):
        pass

    def update(self) -> Car|None:
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
        if p_directions[-1]:  # this is the chance to stay where we are
            dot_path = mpath.Path.unit_circle()
            t = Affine2D().scale(p_directions[-1] * 10 * scale)
            vertices.extend(t.transform(dot_path.vertices))
            codes.extend(dot_path.codes)

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
        
        self.marker = mpath.Path(vertices, codes)

        super().__init__(self.marker.vertices, self.marker.codes,closed=False)


class Road(Tile):
    def __init__(self,x:int,y:int,p_directions:np.ndarray,speed_limit=1):
        super().__init__()
        assert(len(p_directions)==9)
        assert np.allclose(1,np.sum(p_directions))
        self._x = x
        self._y = y
        self._directions =  np.array(p_directions,copy=True,dtype=float)
        self.p_directions = np.array(p_directions,copy=True,dtype=float)
        self.speed_limit=speed_limit
        self.car = None
        self.neighbors = [None]*8
    
    @property
    def occupied(self) -> bool:
        return self.car is not None
    
    def move_in(self,car):
        if self.car is not None:
            raise ValueError("Cannot move car into this cell! It already has one!")
        self.car = car
        for i, neighbor in enumerate(self.neighbors):
            if neighbor:
                neighbor_idx = (i+4)%8
                print(neighbor.p_directions)
                prev_val = neighbor.p_directions[neighbor_idx]
                print(f"changing neighbor {i} idx {neighbor_idx} (prev {neighbor.p_directions[neighbor_idx]}) of {neighbor} to 0")
                neighbor.p_directions[neighbor_idx] = 0
                non_zero_connections = np.where(neighbor.p_directions > 0)[0]
                if not len(non_zero_connections):
                    non_zero_connections = [8]
                neighbor.p_directions[non_zero_connections] += prev_val / len(non_zero_connections)
                print(prev_val,neighbor.p_directions,non_zero_connections)
                assert np.allclose(np.sum(neighbor.p_directions),1)
        
    def move_out(self):
    # what to do when a car moves out of our cell
        for i, neighbor in enumerate(self.neighbors):
            if neighbor:
                neighbor_idx_for_me = (i+4)%8  # this is which neighbor we are from the neighboring tile's perspective 
                new_val = neighbor._directions[neighbor_idx_for_me]
                print(f"changing neighbor {i} idx {neighbor_idx_for_me} (prev {neighbor.p_directions[neighbor_idx_for_me]}) of {neighbor} to {neighbor._directions[neighbor_idx_for_me]}")
                non_zero_connections = np.where(neighbor.p_directions > 0)[0]
                if not len(non_zero_connections):
                    non_zero_connections = [8]
                assert(neighbor.p_directions[neighbor_idx_for_me] == 0)
                neighbor.p_directions[non_zero_connections] -= new_val / len(non_zero_connections)
                neighbor.p_directions[neighbor_idx_for_me] = new_val
                print(new_val,neighbor.p_directions,non_zero_connections)
                assert np.allclose(np.sum(neighbor.p_directions),1)
        self.car=None

    def marker(self, scale=1.0):
        return MarkerStyle(RoadMarker(self.p_directions, scale=scale))

    def plot(self,ax,connections=True,markersize=50,**kwargs):
        p = ax.plot(self.x,self.y,marker=self.marker(1),markersize=markersize,**kwargs)
        # ax.text(self.x,self.y,str(self.index),verticalalignment="bottom",horizontalalignment="right")
        c = p[0].get_color()
        if connections:
            for i,n in enumerate(self.neighbors):
                if n is not None and self.p_directions[i] > 0:
                    ax.plot([self.x,n.x],[self.y,n.y], linestyle=("dashed" if i > 3 else "dotted"),alpha=0.5, color=c)
                    # ax.plot([self.x,n.x],[self.y,n.y],linewidth=10*self.p_directions[i], linestyle=("dashed" if i > 3 else "dotted"))
        return p
    
    def __repr__(self):
        return f"Road({self.x},{self.y},occupied={self.occupied})"


class Exit(Road):
    def __init__(self,x,y):
        super().__init__(x,y,[0,0,0,0,0,0,0,0,1.0])
    def move_in(self,car):
        car.to_remove = True
    
    def marker(self, scale=1.0):
        # sq = mpath.Path.unit_rectangle()
        # x = mpath.Path.unit_regular_star(4)
        # sq = sq.transformed(Affine2D().scale(0.5).translate(-0.25,-0.25))
        # x = x.transformed(Affine2D().scale(0.5).translate(-0.25,-0.25))
        # return MarkerStyle(mpath.Path(vertices=np.concatenate([sq.vertices,x.vertices]), codes=np.concatenate([sq.codes,x.codes]), closed=True))
        return MarkerStyle("*")

    @property
    def occupied(self):
        return False
    
class Onramp(Road):
    
    def __init__(self,x,y,p_directions,speed_limit=1,car_period=1,avg_speed=1):
        super().__init__(x,y,p_directions,speed_limit)
        self.timer = 0
        self.car_period = car_period
        self.avg_speed = avg_speed
        
    def update(self):
        if not self.timer % self.car_period:
            if not self.occupied:
                self.timer += 1
                return Car(self,np.ceil(rng.random()*self.avg_speed))
            return None
        self.timer += 1
        return None
    
    def marker(self, scale=1.0):
        # sq = mpath.Path.unit_rectangle()
        # x = mpath.Path.unit_regular_star(4)
        # sq = sq.transformed(Affine2D().scale(0.5).translate(-0.25,-0.25))
        # x = x.transformed(Affine2D().scale(0.5).translate(-0.25,-0.25))
        # return MarkerStyle(mpath.Path(vertices=np.concatenate([sq.vertices,x.vertices]), codes=np.concatenate([sq.codes,x.codes]), closed=True))
        return MarkerStyle("P")