class Car:
    def __init__(self, tile, desired_speed):
        self.tile = tile
        self.desired_speed = desired_speed
        self.moves_left = min(self.desired_speed,self.tile.speed_limit)
        self.to_remove = False
        self.color = "black"
        self.ID = None
        self.timestep_of_creation = None
        self.route = None
        self.route_idx = None  # which step of the way through the route are we

    @property
    def x(self):
        return self.tile.x
    
    @property
    def y(self):
        return self.tile.y
    
    def set_route(self,route):
        self.route = route
        self.route_idx = 0
    
    def set_timestep_of_creation(self,t):
        self.timestep_of_creation = t

    def set_id(self,ID):
        self.ID = ID
    
    def reset(self):
        # reset state at beginning of next cycle
        self.moves_left = min(self.desired_speed,self.tile.speed_limit)

    def set_color(self,color):
        self.color = color

    def setup(self):
        self.tile.move_in(self)
    
    def move_to(self,tile):
        if tile is not self.tile and tile not in self.tile.neighbors:
            raise ValueError(f"Non-adjacent move! Tried to move from {self.tile} to {tile}!")
        if self.moves_left < 1:
            raise ValueError("Tried to move to a tile but no moves left!")
        self.tile.move_out()
        tile.move_in(self)
        self.tile = tile
        self.moves_left-=1
    