from abc import ABC, abstractproperty, abstractmethod
import numpy as np
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D
import matplotlib.path as mpath
import matplotlib.patches as patches
from matplotlib import colormaps
from car import Car 

rng = np.random.default_rng()

class Tile(ABC):
    def __init__(self):
        self.index = None
        self.choice = None
    
    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y

    def add_choice(self,choice):
        self.choice = choice
        choice.attached_tile = self

    def move_in(self,car:Car):
        if self.choice and car.route is None:
            route = self.choice.choose()
            car.set_route(route)

    @abstractmethod
    def move_out(self):
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
        self.carless_directions =  np.array(p_directions,copy=True,dtype=float)
        self.orig_directions =  np.array(p_directions,copy=True,dtype=float)
        self.p_directions = np.array(p_directions,copy=True,dtype=float)
        self.speed_limit=speed_limit
        self.car = None
        self.neighbors = [None]*8
        self.constraints = 0
    
    def reset(self):
        self.p_directions = np.array(self.orig_directions,copy=True,dtype=float)
        self.carless_directions = np.array(self.orig_directions,copy=True,dtype=float)
        self.car = None
        self.constraints = 0

    @property
    def occupied(self) -> bool:
        return self.car is not None
    
    def move_in(self,car:Car):
        if self.car is not None:
            raise ValueError("Cannot move car into this cell! It already has one!")
        self.car = car
        for i, neighbor in enumerate(self.neighbors):
            if neighbor:
                # print(f"Reallocating for tile {neighbor}")
                neighbor_idx_for_me = (i+4)%8  # this is which neighbor we are from the neighboring tile's perspective 
                neighbor.p_directions = self.reallocate(neighbor_idx_for_me,0,neighbor.p_directions)
                neighbor.constraints += 1
        super().move_in(car)

    def reallocate(self,direction,new_val,old_arr):
        # print(f"Setting direction {direction} in arr {old_arr} to {new_val}")
        old_arr = old_arr*(1.0-new_val)
        old_arr[direction] = new_val
        if np.sum(old_arr) == 0:
            old_arr[-1] = 1.0  # stay where you are
        old_arr = old_arr/np.sum(old_arr)
        # print(f"result: {old_arr}")
        return old_arr
        # if new_val == 0:
        #     prev_val = old_arr[direction]
        #     old_arr[direction] = 0
        #     non_zero_connections = np.where(old_arr > 0)[0]
        #     if not len(non_zero_connections):
        #         non_zero_connections = [8]
        #     old_arr[non_zero_connections] += prev_val / len(non_zero_connections)
        #     assert np.allclose(np.sum(old_arr),1)
        #     if not np.all(old_arr >= 0):
        #         raise ValueError(f"Invalid reallocation! old:{old_arr} new_val:{new_val} nonz conns:{non_zero_connections}, direction:{direction}")            # print(f"Set to {old_arr}")
        #     return old_arr
        
        # old_orig = np.array(old_arr,copy=True)
        # non_zero_connections = np.where(old_arr > 0)[0]
        # if not len(non_zero_connections):
        #     non_zero_connections = [8]
        # assert(old_arr[direction] == 0)
        # old_arr[non_zero_connections] -= new_val / len(non_zero_connections)
        # old_arr[direction] = new_val
        # # print(new_val,old_arr,non_zero_connections)
        # assert np.allclose(np.sum(old_arr),1)
        # if not np.all(old_arr >= 0):
        #     raise ValueError(f"Invalid reallocation! old:{old_orig} new:{old_arr} new_val:{new_val} nonz conns:{non_zero_connections}, direction:{direction}")
        # # print(f"Set to {old_arr}")
        # return old_arr
        

    # def block(self,direction):
    #     prev_val = self.p_directions[direction]
    #     # print(f"changing neighbor {i} idx {neighbor_idx} (prev {neighbor.p_directions[neighbor_idx]}) of {neighbor} to 0")
    #     self.p_directions[direction] = 0
    #     non_zero_connections = np.where(self.p_directions > 0)[0]
    #     if not len(non_zero_connections):
    #         non_zero_connections = [8]
    #     self.p_directions[non_zero_connections] += prev_val / len(non_zero_connections)
    #     assert np.allclose(np.sum(self.p_directions),1)
        
    def move_out(self):
    # what to do when a car moves out of our cell
        for i, neighbor in enumerate(self.neighbors):
            if neighbor:
                neighbor_idx_for_me = (i+4)%8  # this is which neighbor we are from the neighboring tile's perspective 
                new_val = neighbor.carless_directions[neighbor_idx_for_me]
                neighbor.p_directions = self.reallocate(neighbor_idx_for_me,new_val,neighbor.p_directions)
                neighbor.constraints -= 1
        self.car=None

    def marker(self, scale=1.0, live_connections:bool=False):
        if live_connections:
            return MarkerStyle(RoadMarker(self.p_directions, scale=scale))
        return MarkerStyle(RoadMarker(self.orig_directions, scale=scale))

    def plot(self,ax,conns=True,live_connections=False,markersize=50,**kwargs):
        p = ax.plot(self.x,self.y,marker=self.marker(1,live_connections),markersize=markersize,**kwargs)[0]
        # ax.text(self.x,self.y,str(self.index),verticalalignment="bottom",horizontalalignment="right")
        artists = [p]
        if conns:
            c = p.get_color()
            conn = self.p_directions if live_connections else self.orig_directions
            for i,n in enumerate(self.neighbors):
                if n is not None and conn[i] > 0:
                    artists.extend(ax.plot([self.x,n.x],[self.y,n.y], linestyle=("dashed" if i > 3 else "dotted"),alpha=0.5, color=c))
                    # ax.plot([self.x,n.x],[self.y,n.y],linewidth=10*self.p_directions[i], linestyle=("dashed" if i > 3 else "dotted"))
        return artists
    
    def __repr__(self):
        return f"Road({self.x},{self.y},occupied={self.occupied})"


class Exit(Road):
    def __init__(self,x,y,direction=None):
        super().__init__(x,y,[0,0,0,0,0,0,0,0,1.0])
        self.exited = {}
        self.timestep = 0

    def update(self):
        self.timestep += 1
        self.exited[self.timestep] = []

    def move_in(self,car):
        car.to_remove = True
        self.exited[self.timestep].append(car)
    
    def marker(self, scale=1.0,live_connections=False):
        return MarkerStyle("*")

    def __repr__(self):
        return f"Exit({self.x},{self.y})"
    
    def reset(self):
        self.timestep = 0
        self.exited = {}

    @property
    def occupied(self):
        return False
    
class Onramp(Road):
    def __init__(self,x,y,p_directions,speed_limit=1,car_period=1,avg_speed=1):
        super().__init__(x,y,p_directions,speed_limit)
        self.timer = 0
        self.car_period = car_period
        self.avg_speed = avg_speed
        self.color = rng.choice(colormaps["Set3"].colors)
        self.enabled = True

    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False

    def reset(self):
        self.timer = 0
        super().reset()

    def update(self):
        if not self.enabled:
            return None
        if not self.timer % self.car_period:
            if not self.occupied:
                self.timer += 1
                c = Car(self,np.ceil(rng.random()*self.avg_speed))
                c.set_color(self.color)
                return c
            return None
        self.timer += 1
        return None
    
    def marker(self, scale=1.0,live_connections=False):
       return MarkerStyle("P")

    def plot(self,ax,live_connections=False,markersize=50,**kwargs):
        kwargs["c"] = self.color
        return super().plot(ax,live_connections=live_connections,markersize=markersize,**kwargs)
    
    def __repr__(self):
        return f"Onramp({self.x},{self.y})"