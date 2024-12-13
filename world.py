import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from tiles import Road, Exit, Onramp, Tile
from traffic_signals import Signaller, Stoplight
rng = np.random.default_rng()
from matplotlib import colormaps
from matplotlib.axis import Axis

class World:
    def __init__(self,tiles,cars) -> None:
        self._tiles = tiles  # this is just a 1d array of tiles
        self.tiles = np.empty((self.max_x+2,self.max_y+2),dtype=object)  # this is a 2d grid of None or Tile
        self.tiles.fill(None)
        for i,t in enumerate(tiles):
            t.set_index(i)
            if self.tiles[t.x,t.y]:
                raise ValueError(f"Error! Overlapping tiles at ({t.x,t.y})!")
            self.tiles[t.x,t.y] = t  
        self.running_car_id = 0 
        self.timestep = 0
        self.markov = None
        self.connect_tiles()
        self.cars = []
        for car in cars:
            self.add_car(car)  
        
        self.car_info_packets = []
        self.signaller = Signaller()
    
    def add_stoplight(self,stoplight):
        self.signaller.add_stoplight(stoplight)
    
    def add_car(self,car):
        car.set_id(self.running_car_id)
        self.running_car_id += 1
        car.set_timestep_of_creation(self.timestep)

        car.set_color(rng.choice(colormaps["Set3"].colors))
        # car.set_color(rng.choice(["tab:red","tab:blue","tab:orange","tab:gray","tab:pink","tab:purple"]))
        self.cars.append(car)
        car.setup()

    def run(self,steps,draw:bool,outpath:str=None,**kwargs):
        if draw and outpath is None:
            raise ValueError("Must specify outpath if you want to draw the world!")
        
        if draw:
            fig, ax = plt.subplots()
            def update(frame):
                ax.cla()
                artists = self.draw(ax=ax,**kwargs)
                self.do_simulation_step()
                return artists
            
            ani = animation.FuncAnimation(fig,update,frames=steps,interval=100,blit=True)
            ani.save(filename=outpath, writer="pillow",dpi=150)
        else:
            for _ in range(steps):
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
            t.carless_directions = np.array(t.p_directions,copy=True)
            t.orig_directions = np.array(t.p_directions,copy=True)
        assert np.all(self.markov >= 0)
        assert np.allclose(1,np.sum(self.markov[:,:])/self.markov.shape[0])

    def draw(self,shift=0.5,ax=None,conns=True,live_connections=False,show=True,xlims=None,ylims=None,**kwargs):
        artists = []
        if ax is None:
            fig, ax = plt.subplots()
        for r in self._tiles:
            artists.extend(r.plot(ax,conns=conns,live_connections=live_connections,zorder=0,**kwargs))
        xticks = np.arange(self.max_x+2) - 1 + shift
        yticks = np.arange(self.max_y+2) - 1 + shift

        # NO KWARGS
        artists.extend(self.signaller.draw(ax))
        # artists.extend(self.signaller.draw(ax,**kwargs))

        # xlim = xlims or ax.get_xlim()
        # ylim = ylims or ax.get_ylim()

        for car in self.cars:
            artists.append(ax.scatter(car.x,car.y,marker="s",s=20,color=car.color,zorder=10))
            if car.route is not None:
                artists.extend(car.route.draw(ax,idx=car.route_idx, alpha=0.2, color=car.color))

        ax.set_title(f"t={self.timestep}")
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        if xlims is not None:
            ax.set_xlim(*xlims)
        if xlims is not None:
            ax.set_ylim(*ylims)
        ax.set_aspect('equal')
        ax.grid(which="major")
        if show:
            plt.show()
        return artists

    def do_simulation_step(self):
        # reset cars to their initial states
        # pick a random order (?) to drive cars in
        # drive each car until it's out of moves
        self.signaller.update(self.timestep)
        if self.timestep % 100 == 0:
            print(f"====  t={self.timestep} ====")
        self.cars = [c for c in self.cars if not c.to_remove]
        # if not len(self.cars):
        #     return
        for car in self.cars:
            car.reset()
        car_info_packets = []

        # driving_order = np.arange(len(self.cars))
        # rng.shuffle(driving_order)
        # print("driving order:",driving_order)
        done_driving = []
        while len(done_driving) < len([c for c in self.cars if not c.to_remove]):
            tiles_w_cars = [t for t in self._tiles if t.occupied]
            tiles_w_cars.sort(key=lambda t: t.constraints)
            for car in [t.car for t in tiles_w_cars if t.car.ID not in done_driving]:
                if not car.moves_left:
                    done_driving.append(car.ID)
                    car_info_packets.append([car.ID,car.tile.x,car.tile.y])
                    continue
                tiles = car.tile.neighbors+[car.tile]
                try:
                    next_tile = rng.choice(car.tile.neighbors+[car.tile],p=car.tile.p_directions)
                except ValueError as e:
                    print(f"ERROR in sim step: {e}")
                    print(f"Tile: {car.tile}")
                    print(f"Probs: {car.tile.p_directions}")
                    raise e
                if car.route is not None:
                    route_tile = car.route.tiles[car.route_idx]
                    if route_tile not in tiles:
                        print(f"WARNING Route {car.route} wants car {car.ID} to go to tile {route_tile} from {car.tile} but it's not a neighbor!")
                        next_tile = car.tile
                    elif car.tile.p_directions[car.tile.neighbors.index(route_tile)] == 0:  # miserable
                        # print(car.tile.p_directions, car.tile.neighbors.index(route_tile))              
                        next_tile = car.tile
                    else:
                        if len(car.route.tiles) - 1 ==  car.route_idx:
                            car.set_route(None)
                            # print(f"Car {car.ID} is on its last step of its route :D")
                        else:
                            car.route_idx += 1
                        next_tile = route_tile
                        # print(f"Car {car.ID} is following route {car.route} from {car.tile} to {route_tile} :)")
                # print(f"car {car.ID}: I'm going to {next_tile}!")
                car.move_to(next_tile)
        self.car_info_packets.append(np.array(car_info_packets))
        self.timestep += 1

        for tile in self._tiles:
            res = tile.update()
            if res is not None:  # then its a car given to us by a ramp tile
                # print(res)
                self.add_car(res)

    def reset(self):
        self.signaller.reset()
        for car in self.cars:
            del(car)
        self.cars = []
        for tile in self._tiles:
            tile.reset()
        self.timestep = 0
        self.car_info_packets = []
        self.running_car_id = 0

    def __getitem__(self, index):
        return self.tiles[index]

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
        return min([t.y for t in self._tiles])

class Route:
    def __init__(self,tiles:list[Tile]):
        self.tiles = [t for t in tiles if t is not None]
        if len(self.tiles) < 1:
            raise ValueError("Route must have at least one tile!")
        self.tile_ids = [t.index for t in self.tiles]

    def __len__(self):
        return len(self.tiles)
    
    def __repr__(self):
        return repr(self.tiles)
    
    def draw(self,ax:Axis,idx=0,**kwargs):
        x,y = zip(*[(t.x,t.y) for t in self.tiles[idx:]])
        artists = []
        # for tile in self.tiles:
            # tile.plot(ax,**kwargs)
        artists.extend(ax.plot(x,y,**kwargs,zorder=5))
        second = self.tiles[-2]
        last = self.tiles[-1]
        kw = {"color":artists[0].get_color(), "alpha":kwargs.get("alpha",1) * 0.5}
        artists.append(ax.arrow(second.x,second.y,0.5*(last.x-second.x),0.5*(last.y-second.y),**kw,zorder=5,width=0.15))
        return artists
        # ax.scatter(x,y,marker="o",**kwargs,zorder=5)

class Choice:
    def __init__(self,routes:list[Route],probabilities):
        assert np.allclose(np.sum(probabilities),1)
        assert len(probabilities) == len(routes)
        self.probabilities = probabilities
        self.routes = routes
    
    def choose(self):
        return rng.choice(self.routes,p=self.probabilities)