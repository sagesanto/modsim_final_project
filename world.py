import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from tiles import Road, Exit, Onramp
rng = np.random.default_rng()

class World:
    def __init__(self,tiles,cars) -> None:
        self._tiles = tiles  # this is just a 1d array of tiles
        self.tiles = np.empty((self.max_x+2,self.max_y+2),dtype=object)  # this is a 2d grid of None or Tile
        self.tiles.fill(None)
        for i,t in enumerate(tiles):
            t.set_index(i)
            self.tiles[t.x,t.y] = t  
        self.running_car_id = 0 
        self.timestep = 0
        self.markov = None
        self.connect_tiles()
        self.cars = []
        for car in cars:
            self.add_car(car)  
        
        self.car_info_packets = []
    
    def add_car(self,car):
        car.set_id(self.running_car_id)
        car.set_timestep_of_creation(self.timestep)
        self.running_car_id += 1
        car.set_color(rng.choice(["tab:red","tab:blue","tab:orange","tab:gray","tab:pink","tab:purple"]))
        self.cars.append(car)
        car.setup()

    def run(self,steps,draw:bool,outpath:str=None,**kwargs):
        if draw and outpath is None:
            raise ValueError("Must specify outpath if you want to draw the world!")
        
        if draw:
            fig, ax = plt.subplots()
            def update(frame):
                ax.cla()
                self.draw(ax=ax,**kwargs)
                self.do_simulation_step()
            
            ani = animation.FuncAnimation(fig,update,frames=steps,interval=250)
            ani.save(filename=outpath, writer="pillow",dpi=150)
        else:
            for _ in steps:
                self.do_simulation_step()

    
    def connect_tiles(self):
        self.markov = np.zeros((len(self._tiles),len(self._tiles)))
        for j,t in enumerate(self._tiles):
            to_reallocate = 0
            for i, (dx,dy) in enumerate([(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]):
                x,y = t.x+dx, t.y+dy
                if x < 0 or y < 0:
                    t.neighbors[i] = None
                    to_reallocate += t.p_directions[i]
                    t.p_directions[i] = 0
                    continue
                other = self.tiles[x,y]
                t.neighbors[i] = other
                if other is None or isinstance(other,Onramp):
                    to_reallocate += t.p_directions[i]
                    t.p_directions[i] = 0
            non = np.where(t.p_directions != 0)[0]
            if not len(non):
                non = [8] # stay still 
            t.p_directions[non] += to_reallocate/len(non)

            for i,other in enumerate(t.neighbors):
                if other is None:
                    continue
                self.markov[t.index,other.index] = t.p_directions[i]
            self.markov[t.index,t.index] = t.p_directions[-1]

            # technically, could speed this up by keeping track of tiles we've visited and recording that 
            # this tile is like the (-i)th neighbor of the other tile (or something like that), then doing a recursive thing.
            # however i haven't had coffee yet, nor have i thought abt doing this elegantly, nor do i care
        # print([(a,np.sum(self.markov[a,:])) for a in np.arange(self.markov.shape[0])])
        for t in self._tiles:
            t._directions = np.array(t.p_directions,copy=True)
        assert np.allclose(1,np.sum(self.markov[:,:])/self.markov.shape[0])

    def draw(self,shift=0.5,ax=None,connections=True,**kwargs):
        if ax is None:
            fig, ax = plt.subplots()
        for r in self._tiles:
            r.plot(ax,connections=connections,**kwargs)
        xticks = np.arange(self.max_x+2) - 1 + shift
        yticks = np.arange(self.max_y+2) - 1 + shift
        for car in self.cars:
            ax.scatter(car.x+0.2,car.y+0.2,marker="s",s=75,color=car.color)

        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect('equal')
        ax.grid(which="major")
        plt.show()

    def do_simulation_step(self):
        # reset cars to their initial states
        # pick a random order (?) to drive cars in
        # drive each car until it's out of moves
        for tile in self._tiles:
            res = tile.update()
            if res is not None:  # then its a car given to us by a ramp tile
                self.add_car(res)

        self.cars = [c for c in self.cars if not c.to_remove]
        if not len(self.cars):
            return
        for car in self.cars:
            car.reset()
        car_info_packets = []
        driving_order = np.arange(len(self.cars))
        rng.shuffle(driving_order)
        # print("driving order:",driving_order)
        done_driving = []
        while len(done_driving) < len(self.cars):
            for i in [c for c in driving_order if c not in done_driving]:
                car = self.cars[i]
                if not car.moves_left:
                    done_driving.append(i)
                    car_info_packets.append([car.ID,car.tile.x,car.tile.y])
                    continue
                next_tile = rng.choice(car.tile.neighbors+[car.tile],p=car.tile.p_directions)
                print(f"car {car}: I'm going to {next_tile}!")
                car.move_to(next_tile)
        self.car_info_packets.append(np.array(car_info_packets))
        self.timestep += 1

    @property
    def max_x(self):
        return max([t.x for t in self._tiles])
    
    @property
    def min_x(self):
        return min([t.x for t in self._tiles])
    
    @property
    def max_y(self):
        return max([t.y for t in self._tiles])
    
    @property
    def min_y(self):
        return max([t.y for t in self._tiles])