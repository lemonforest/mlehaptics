import numpy as np
from doom_raycast import bresenham_ray

class SheafRay:
    """
    Models a ray as a directed sheaf where restriction maps are 1.0 (pass) or 0.0 (block).
    """
    def __init__(self, start, end, grid):
        self.path = bresenham_ray(start[0], start[1], end[0], end[1])
        self.grid = grid
        self.n = len(self.path)
        
        # Restriction maps (edges between cells in the path)
        self.restrictions = []
        for i in range(self.n - 1):
            curr_cell = self.path[i]
            next_cell = self.path[i+1]
            
            # If the next cell is a wall, the restriction map is 0
            if grid[next_cell[0], next_cell[1]] == 0:
                self.restrictions.append(0.0)
            else:
                self.restrictions.append(1.0)

    def get_sheaf_laplacian(self):
        """
        Constructs a 1D Laplacian for the ray path.
        L_ij = -restriction(i,j) if adjacent, else sum of restrictions for diagonal.
        """
        L = np.zeros((self.n, self.n))
        for i in range(self.n - 1):
            r = self.restrictions[i]
            L[i, i] += r
            L[i+1, i+1] += r
            L[i, i+1] = -r
            L[i+1, i] = -r
        return L

    def find_absorption_point(self):
        """
        The first zero restriction map indicates where the ray is absorbed.
        """
        for i, r in enumerate(self.restrictions):
            if r == 0.0:
                return self.path[i+1]
        return None

if __name__ == "__main__":
    grid = np.ones((10, 10))
    grid[5, 5] = 0 # Wall
    
    start = (0, 0)
    end = (9, 9)
    
    sheaf = SheafRay(start, end, grid)
    print("Ray Path:", sheaf.path)
    print("Restrictions:", sheaf.restrictions)
    
    L = sheaf.get_sheaf_laplacian()
    print("\nSheaf Laplacian (first 5x5 block):\n", L[:5, :5])
    
    hit = sheaf.find_absorption_point()
    print("\nAbsorption (Hit) Point:", hit)
