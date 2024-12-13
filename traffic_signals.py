import numpy as np

class Stoplight:
    def __init__(self,tile,direction:int,period=10,offset=0,on_to_half_p_ratio=1,name=None):
        if not isinstance(direction,int):
            raise ValueError(f"Direction should be an integer direction index, not {type(direction)}!")
        self.attached_tile = tile
        self.direction = direction
        self.affected_tile = tile.neighbors[self.direction]
        self.period = period
        self.offset = offset
        self.delay = np.sin((1-on_to_half_p_ratio)/2*np.pi)
        self.update_func = self.default_update_func(self.period,self.offset,self.delay)
        self.stopped = False
        self.gos = []
        self.stops = []
        self.name = name
    
    @staticmethod
    def first_zero(P,on_to_half_p_ratio=None,vertical_shift=None):
        if vertical_shift is None and on_to_half_p_ratio is None:
            raise ValueError("One of on_to_off_ratio or vertical_shift must not be None!")
        if vertical_shift is not None and on_to_half_p_ratio is not None:
            raise ValueError("Only one of on_to_off_ratio or vertical_shift should be not-None!")
        if vertical_shift is not None:
            D = vertical_shift
        else:
            D = np.sin((1-on_to_half_p_ratio)/2*np.pi)
        return P*np.asin(D)/(2*np.pi)

    @property
    def x(self):
        return self.attached_tile.x
    
    @property
    def y(self):
        return self.attached_tile.y

    def default_update_func(self,period,offset,vertical_shift):
        first_zero = Stoplight.first_zero(period,vertical_shift=vertical_shift)
        return lambda t,p=period: int(np.sin((2*np.pi/p)*(t-offset+first_zero))-vertical_shift >= 0)
    
    # should take t as an argument and return 0 (off) or 1 (on)
    def set_update_func(self,f):
        self.update_func=f

    def update(self,t):
        r = self.update_func(t)
        if r:
            return self.go(t)
        self.stop(t)
    
    def __repr__(self):
        return f"Stoplight ({'red' if self.stopped else 'green'}) on {self.attached_tile}, affecting {self.affected_tile}"
    
    def reset(self):
        self.go(0)
        self.gos = []
        self.stops = []

    # NOTE: this logic breaks down if there is more than one stoplight *facing the same direction* on a given tile (there shouldn't be)

    def stop(self,t):
        if self.affected_tile is None:
            raise ValueError(f"Stoplight {self} affected tile is None!")
            # print("Warning! Stoplight affected tile is None!")
            # return
        # need to make sure that cars leaving a cell don't re-enable the connection that the stoplight is preventing
        if not self.stopped:
            # print(f"Stopping traffic on {self.affected_tile}")
            # print("before reallocation:",self.affected_tile.p_directions)
            self.affected_tile.carless_directions = self.affected_tile.reallocate((self.direction+4)%8,0,self.affected_tile.carless_directions)
            self.affected_tile.p_directions = self.affected_tile.reallocate((self.direction+4)%8,0,self.affected_tile.p_directions)
            # print("after reallocation:",self.affected_tile.p_directions)
            self.stopped = True
            self.affected_tile.constraints += 1
            self.stops.append(t)
    
    def go(self,t):
        if self.affected_tile is None:
            raise ValueError(f"Stoplight {self} affected tile is None!")
            # print("Warning! Stoplight affected tile is None!")
            # return
        if self.stopped:
            # print(f"Allowing traffic on {self.affected_tile}")
            self.stopped = False
            old_val = self.affected_tile.orig_directions[(self.direction+4)%8]
            self.affected_tile.carless_directions = self.affected_tile.reallocate((self.direction+4)%8,old_val,self.affected_tile.carless_directions)
            self.gos.append(t)
            self.affected_tile.constraints -= 1

            if not self.attached_tile.occupied:
                self.affected_tile.p_directions = self.affected_tile.reallocate((self.direction+4)%8,old_val,self.affected_tile.p_directions)

    def draw(self,ax,**kwargs):
        # want to clockwise rotate [0,1] by our direction
        theta = -self.direction * np.pi/4  # want clockwise rotation
        x_off = 0 * np.cos(theta) - 1 * np.sin(theta)
        y_off = 0 * np.sin(theta) + 1 * np.cos(theta)
        return ax.plot(self.x+x_off/2,self.y+y_off/2,marker=".",**kwargs,c="tab:red" if self.stopped else "tab:green")

class Signaller:
    def __init__(self):
        self.stoplights = []

    def add_stoplight(self,stoplight:Stoplight):
        self.stoplights.append(stoplight)
    
    def update(self,t):
        for s in self.stoplights:
            s.update(t)
    
    def draw(self,ax,**kwargs):
        artists = []
        for s in self.stoplights:
            artists.extend(s.draw(ax,**kwargs))
        return artists
        
    def reset(self):
        for s in self.stoplights:
            s.reset()
