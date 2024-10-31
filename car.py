
class Car:
    def __init__(self, tile, desired_speed):
        self.tile = tile
        self.desired_speed = desired_speed
        self.moves_left = min(self.desired_speed,self.tile.speed_limit)

    @property
    def x(self):
        return self.tile.x
    
    @property
    def y(self):
        return self.tile.y
    
    def reset(self):
        # reset state at beginning of next cycle
        self.moves_left = min(self.desired_speed,self.tile.speed_limit)
    
    def move_to(self,tile):
        if self.moves_left < 1:
            raise ValueError("Tried to move to a tile but no moves left!")
        self.tile = tile
        self.moves_left-=1
    