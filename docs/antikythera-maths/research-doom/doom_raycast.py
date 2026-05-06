import numpy as np

def bresenham_ray(x0, y0, x1, y1):
    """
    Standard Bresenham's line algorithm to find grid cells traversed by a ray.
    """
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    
    cells = []
    while True:
        cells.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return cells

class Raycaster:
    def __init__(self, grid_size=(64, 64)):
        self.grid_size = grid_size
        self.grid = np.ones(grid_size) # 1 = Air, 0 = Wall

    def set_wall(self, x, y):
        if 0 <= x < self.grid_size[0] and 0 <= y < self.grid_size[1]:
            self.grid[x, y] = 0

    def cast_ray(self, start, end):
        path = bresenham_ray(start[0], start[1], end[0], end[1])
        
        hit_point = None
        for x, y in path:
            if not (0 <= x < self.grid_size[0] and 0 <= y < self.grid_size[1]):
                break
            if self.grid[x, y] == 0:
                hit_point = (x, y)
                break
        
        return path, hit_point

if __name__ == "__main__":
    rc = Raycaster((10, 10))
    rc.set_wall(5, 5)
    rc.set_wall(5, 6)
    
    start = (1, 1)
    end = (8, 8)
    path, hit = rc.cast_ray(start, end)
    
    print(f"Ray from {start} to {end}")
    print(f"Path: {path}")
    print(f"Hit Point: {hit}")
