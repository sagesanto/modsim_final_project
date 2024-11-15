class Stoplight:
    def __init__(self,tile,direction:int):
        self.attached_tile = tile
        self.direction = direction
        self.affected_tile = tile.neighbors[self.direction]
    
    def stop(self):
        if self.affected_tile is None:
            print("Warning! Stoplight affected tile is None!")
            return
        # need to make sure that cars leaving a cell don't re-enable the connection that the stoplight is preventing
        self.affected_tile.carless_directions[(self.direction+4)%8] = 0
        self.affected_tile.p_directions[(self.direction+4)%8] = 0
    
    def go(self):
        if self.affected_tile is None:
            print("Warning! Stoplight affected tile is None!")
            return
        self.affected_tile.carless_directions[(self.direction+4)%8] = self.affected_tile.orig_directions[(self.direction+4)%8]


class Signaller:
    pass