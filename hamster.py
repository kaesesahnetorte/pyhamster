
"""
provide full python code for the following app:

It is a top down tilemap simulator where a hamster can move around.
In the code, the tiles are encoded as a 2d array where each tile type has a different code:
The tile types are:
1. obstacle tile (encoded as X)
2. empty tile with any number of food pieces on it. (encoded as integer number equal to the number of food pieces.)
In the code there is a section for the user to implement code for the hamster behavior.
The following functions are implemented to be used by the user:
1. isFree() checks if the tile in front of the hamster is not an obstacle tile
2. forward() makes the hamster go forward one tile. If there is an obstacle there, the simulation ends.
3. turnLeft() makes the hamster turn left relative to its previous facing direction. It stays on the same tile.
4. turnRight() analogous to turnLeft
5. countFood() returns the integer amount of food pieces available on the field the hamster is standing on.
4. takeFood() takes one piece of food from the tile the hamster is standing on if available.
5. putFood() puts one piece of food on the tile the hamster is standing on.

The GUI has the following input options:
1. a "play / pause" button for the simulation time
2. a "single step" button to advance the simulation by just one time frame.
3. a speed slider to adjust the speed of the simulation on playback.
4. a reset button to reset the simulation to the original state.

The original state of the simulation can be set via the map array.
"""



import math
import random
import tkinter as tk
from PIL import Image, ImageTk
import os


# Constants for tile types

EMPTY = 0
X = 'X'
OBSTACLE = X

# Directions: 0 = Up, 1 = Right, 2 = Down, 3 = Left
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class Hamster:
    def __init__(self, x, y, tilemap):
        self.map = tilemap
        self.x = x
        self.y = y
        self.direction = 2  # Start facing Up

    def isFree(self):
        dx, dy = DIRECTIONS[self.direction]
        next_x, next_y = self.x + dx, self.y + dy
        return 0 <= next_x < len(self.map[0]) and 0 <= next_y < len(self.map) and self.map[next_y][next_x] != OBSTACLE

    def forward(self):
        if self.isFree():
            dx, dy = DIRECTIONS[self.direction]
            self.x += dx
            self.y += dy
        else:
            print("Obstacle encountered! Simulation ends.")

    def turnLeft(self):
        self.direction = (self.direction - 1) % 4

    def turnRight(self):
        self.direction = (self.direction + 1) % 4

    def countFood(self):
        if isinstance(self.map[self.y][self.x], int):
            return self.map[self.y][self.x]
        else:
            return 0

    def takeFood(self):
        if self.countFood() > 0:
            self.map[self.y][self.x] -= 1

    def putFood(self):
        if isinstance(self.map[self.y][self.x], int):
            self.map[self.y][self.x] += 1


class TilemapSimulator:
    def __init__(self, master, tilemap, hamster, cb_behavior):
        self.tile_size = 60
        self.master = master
        self.original_tilemap = tilemap
        self.map = self.original_tilemap
        self.map_w = len(self.map[0])
        self.map_h = len(self.map)
        self.hamster = hamster  # Starting position
        self.running = False
        self.speed = 100  # Default speed in milliseconds
        self.cb_behavior = cb_behavior
        hamster_image_path = os.path.join(os.path.dirname(__file__), "hamster.png")
        self.hamster_image = Image.open(hamster_image_path).resize((int(self.tile_size / 2), int(self.tile_size / 2)), Image.LANCZOS)
        self.hamster_photo = ImageTk.PhotoImage(self.hamster_image)

        self.cnv_brd = self.tile_size / 2 # canvas border
        cnv_w = self.cnv_brd *2 + self.tile_size * self.map_w
        cnv_h = self.cnv_brd *2 + self.tile_size * self.map_h
        self.canvas = tk.Canvas(master, width=cnv_w, height=cnv_h)
        self.canvas.pack()

        self.play_pause_button = tk.Button(master, text="Play / Pause", width=10, command=self.toggle_simulation)
        self.play_pause_button.pack()

        self.single_step_button = tk.Button(master, text="Single Step", width=10, command=self.single_step)
        self.single_step_button.pack()

        self.reset_button = tk.Button(master, text="Reset", width=10, command=self.reset)
        self.reset_button.pack()

        self.speed_slider = tk.Scale(master, from_=0, to=100, label="Speed (Hz)", orient=tk.HORIZONTAL, length=300)
        self.speed_slider.set(self.speed)
        self.speed_slider.pack()

        self.reset()
        # self.update_canvas()
        rate: int = int(1000 / (1 + math.pow(2, (self.speed -50) / 10)))
        self.master.after(rate, self.update)

    def toggle_simulation(self):
        self.running = not self.running

    def single_step(self):
        self.update_hamster()

    def reset(self):
        self.map = self.original_tilemap  # Reset tilemap
        self.hamster = Hamster(1, 1, self.map)  # Reset hamster position
        self.update_canvas()

    def update(self):
        if self.running:
            self.update_hamster()
        rate: int = int(1000 / (1 + math.pow(2, (self.speed_slider.get() -50 ) / 10)))
        # rate = int(1000 / self.speed_slider.get())
        self.master.after(rate, self.update)

    def update_hamster(self):
        self.cb_behavior(self.hamster)
        self.update_canvas()

    def update_canvas(self):
        self.canvas.delete("all")
        for y, row in enumerate(self.map):
            for x, tile in enumerate(row):
                x1 = self.cnv_brd + self.tile_size * x
                y1 = self.cnv_brd + self.tile_size * y
                x2 = self.tile_size + x1
                y2 = self.tile_size + y1
                if tile == OBSTACLE:
                    # Draw the obstacle with a border
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="Dark Gray", outline="gray", width=3)
                    # Draw the "X" shape in the center
                    brd = self.tile_size / 8
                    self.canvas.create_line(x1 + brd, y1 + brd, x2 - brd, y2 - brd, fill="gray", width=4)
                    self.canvas.create_line(x2 - brd, y1 + brd, x1 + brd, y2 - brd, fill="gray", width=4)
                else:
                    food_count = tile
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="gray", width=3)
                    if food_count > 0:
                        self.canvas.create_text(x1 + self.tile_size / 2, y1 + self.tile_size / 2, text=str(food_count), font=("Arial", 16))

        # Draw the hamster
        angle = self.hamster.direction * -90 + 180  # 0, 90, 180, 270 degrees
        self.current_hamster_image = ImageTk.PhotoImage(self.hamster_image.rotate(angle, expand=True))
        hamster_x = self.cnv_brd + self.hamster.x * self.tile_size + self.tile_size / 2
        hamster_y = self.cnv_brd + self.hamster.y * self.tile_size + self.tile_size / 2
        # self.canvas.create_oval(hamster_x - 15, hamster_y - 15, hamster_x + 15, hamster_y + 15, fill="orange")
        self.canvas.create_image(hamster_x, hamster_y, image=self.current_hamster_image)


def create_map():
    return [
        [X, X, X, X, X, X, X, X],
        [X, 0,90, 0, 0, 0, 0, X],
        [X, 0, 0, 1, 0, X, 0, X],
        [X, 0, 0, 0, X, X, 0, X],
        [X, X, X, 0, 0, 0, 0, X],
        [X, 0, 0, 0, 0, 0, 0, X],
        [X, 0, 0, 0, 0, 0, 0, X],
        [X, 0, 0, 0, 0, 0, 0, X],
        [X, X, X, X, X, X, X, X],
    ]


def custom(hamster):
        # Example behavior: Move forward if free, else turn right
    hamster.turnLeft()
    while not hamster.isFree():
        hamster.turnRight()
    hamster.forward()
    if hamster.countFood() > 0:
        print("Mhhm")
        hamster.takeFood()
    return


# Main application
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Hamster Tilemap Simulator")
    
    map = create_map()
    hamster = Hamster(1, 1, map)
    simulator = TilemapSimulator(root, map, hamster, custom)

    # custom(hamster)
    root.mainloop()



# Todos
# 1. better obstacle texture
# 2. hamster with visible direction
# 3. greater map
# 4. delete hamster code

