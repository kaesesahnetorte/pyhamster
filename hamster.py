
# sudo dnf install python3-pip
# sudo dnf install python3-tkinter
# pip install numpy pillow sortedcontainers


from copy import copy, deepcopy
import math
from time import sleep, time

import os, sys
import tkinter as tk
from PIL import Image, ImageTk

from sortedcontainers import SortedList, SortedDict
import numpy as np
from enum import Enum, IntEnum

# Constants for tile types
EMPTY = 0
X = -1
OBSTACLE = X



# Axes convention: right-down
class Dir(IntEnum):
    RIGHT: int = 0,
    DOWN: int = 1
    LEFT: int = 2
    UP: int = 3

    def getVec(dircode: int):
        dir_code = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        return dir_code[dircode]
    
    def getCode(vec):
        dir_vec = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
        return dir_vec[tuple(vec)]
# dir_vecs: 0 = Up, 1 = Right, 2 = Down, 3 = Left


class Hamster:

    # pos = (0, 0)
    # dir = (0, 1)
    # tilemap
    # mouth_food

    # cb_reset: callable
    # cb_gameover: callable

    def __init__(self, pos, dir, mouth_food = 0, tilemap = None, cb_gameover = lambda: None, cb_reset = lambda: None):
        self.pos = pos
        self.dir = dir  # Start facing Up
        self.mouth_food: int = mouth_food

        self.cb_gameover: callable = cb_gameover
        self.cb_reset: callable = cb_reset  # Callback for reset
        self.tilemap: any = tilemap
        return

    def bindSim(self, cb_gameover, cb_reset, tilemap):
        self.cb_gameover = cb_gameover
        self.cb_reset = cb_reset
        self.tilemap = tilemap
        return

    def getPos(self):
        return self.pos
    
    def getDir(self):
        return self.dir

    def isFree(self):
        vec_frwrd = self.pos + self.dir

        # out of bounds
        if vec_frwrd[0] < 0 or vec_frwrd[1] < 0:
            return False
        if vec_frwrd[0] >= len(self.tilemap) or vec_frwrd[1] >= len(self.tilemap[0]):
            return False
        
        # obstacle check
        if self.tilemap[vec_frwrd[0]][vec_frwrd[1]] == OBSTACLE:
            return False
        return True
    
    def countMouthFood(self):
        if not isinstance(self.tilemap[self.pos[0]][self.pos[1]], np.int64):
            print("countMouthFood(): Something went wrong! Tile value is not an integer.")
            return 0
        return self.tilemap[self.pos[0]][self.pos[1]]

    def countFloorFood(self):
        if not isinstance(self.tilemap[self.pos[0]][self.pos[1]], np.int64):
            print("countFloorFood(): Something went wrong! Tile value is not an integer.")
            return 0
        return self.tilemap[self.pos[0]][self.pos[1]]

    def forward(self):
        if self.isFree():
            self.pos = np.add(self.pos, self.dir)
        else:
            self.cb_gameover("You crashed into an obstacle! Use isFree() to avoid this.")
        self.sim_step()
        return

    def turnLeft(self):
        mat_left = [[0, 1],
                    [-1, 0]]
        self.dir = np.matmul(mat_left, self.dir)
        self.sim_step()
        return

    def turnRight(self):
        mat_right = [[0, -1],
                     [1, 0]]
        self.dir = np.matmul(mat_right, self.dir)
        self.sim_step()
        return

    def takeFood(self, num: int = 1):
        if num < 0:
            self.cb_gameover("You tried to take a negative amount of food! Only positive values allowed.")
        if self.countFloorFood() < num:
            self.cb_gameover("You tried to take more food than available! Use countFloorFood() to void this.")
        self.mouth_food += num
        self.tilemap[self.pos[0]][self.pos[1]] -= num
        self.sim_step()
        return

    def putFood(self, num: int = 1):
        if num < 0:
            self.cb_gameover("You tried to put down a negative amount of food! Only positive values allowed.")
        if self.mouth_food < num:
            self.cb_gameover("You tried to put food that you do not have in your mouth! Use countMouthFood() to avoid this.")
        if not isinstance(self.tilemap[self.pos[0]][self.pos[1]], np.int64):
            print("putFood(): Something went wrong! Tile value is not an integer.")
            return
        self.mouth_food -= num
        self.tilemap[self.pos[0]][self.pos[1]] += num
        self.sim_step()
        return
    
    def wait(self):
        self.sim_step()
        return

    def sim_step(self):
        self.cb_reset()
        return


class SimulationResetException(Exception):
    """Custom exception to handle simulation reset."""
    pass


class TilemapSimulator:

    def __init__(self, master, tilemap, hamster, cb_behavior):
        self.original_tilemap = deepcopy(tilemap)
        self.tilemap = deepcopy(self.original_tilemap)
        self.original_hamster = deepcopy(hamster)

        self.cb_behavior = cb_behavior
        self.master = master

        self.tile_size = 60

        self.do_term = False
        self.do_reset = False  # Flag for reset
        self.is_running = False
        self.map_size = np.array((len(self.tilemap), len(self.tilemap[0])), dtype=int)

        self.master.protocol("WM_DELETE_WINDOW", self.cb_close)

        # In the TilemapSimulator class __init__ method, modify the hamster image loading line:
        hamster_image_path = os.path.join(os.path.dirname(__file__), "hamster.png")
        self.hamster_image = Image.open(hamster_image_path).resize((int(self.tile_size / 2), int(self.tile_size / 2)), Image.LANCZOS)
        self.hamster_photo = ImageTk.PhotoImage(self.hamster_image)

        self.cnv_bndry = self.tile_size / 2  # canvas border
        cnv_size = self.map_size
        cnv_size *= self.tile_size
        cnv_size += np.full((2), self.cnv_bndry * 2, dtype=int)
        self.canvas = tk.Canvas(master, width=cnv_size[0], height=cnv_size[1])
        self.canvas.pack()

        self.button_play = tk.Button(master, width=10, command=self.cb_button_play)
        self.button_play.pack()

        self.button_step = tk.Button(master, text="Step", width=10, command=self.cb_button_step)
        self.button_step.pack()
        self.button_reset = tk.Button(master, text="Reset", width=10, command=self.cb_button_reset)
        self.button_reset.pack()

        self.slider_speed = tk.Scale(master, from_=0, to=100, label="Speed", orient=tk.HORIZONTAL, length=300)
        self.slider_speed.set(50)
        self.slider_speed.pack()

        self.init_sim()
        return
    
    def init_sim(self):
        self.tilemap = deepcopy(self.original_tilemap)

        self.hamster = deepcopy(self.original_hamster)
        self.hamster.bindSim(self.cb_game_over, self.cb_sim_step, self.tilemap)

        self.scheduled_steps = 0
        self.is_running = False
        self.button_play.config(text="Play")
        self.button_step['state'] = tk.NORMAL
        self.button_play['state'] = tk.NORMAL
        self.button_reset['state'] = tk.DISABLED
        self.update_canvas()
        return

    def sim_main(self):
        while not self.do_term:
            self.init_sim()

            try:
                self.cb_sim_step()
                self.cb_behavior(self.hamster)

                print("Finished behavior!")
                self.cb_game_over()
            except SimulationResetException:
                self.do_reset = False
        return

    def cb_button_play(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.button_play.config(text="Pause")
            self.button_step['state'] = tk.DISABLED
        else:
            self.button_play.config(text="Play")
            self.button_step['state'] = tk.NORMAL
        self.update_canvas()
        return
    
    def cb_button_step(self):
        # not incrementing, but setting to 1
        self.scheduled_steps = 1
        return

    def cb_button_reset(self):
        self.do_reset = True  # Set the reset flag
        self.update_canvas()  # Update the canvas to reflect the reset state
        return
    
    def cb_close(self):
        # terminate cleanly
        self.do_term = True
        self.master.destroy()
        return

    def cb_game_over(self, text: str = ""):
        if len(text) > 0:
            print("Game Over - ", text)
        self.is_running = False
        self.button_step['state'] = tk.DISABLED
        self.button_play['state'] = tk.DISABLED
        self.update_canvas()
        while True:
            self.master.update()
            if self.do_reset or self.do_term:
                break
        # sys.exit()
        return

    def cb_sim_step(self):
        self.update_canvas()

        delay_s: float = 1.0 / (1 + math.pow(2, (self.slider_speed.get() -50 ) / 10))
            
        # active wait for simulation time step delay
        # while updating GUI
        ts_delay_end = time() + delay_s # timestamp
        while time() < ts_delay_end:
            sleep(0.001) # 1ms
            self.master.update()

        # active wait for go-forward
        # while updating GUI
        while True:
            self.master.update()

            if self.do_reset or self.do_term:
                raise SimulationResetException()
                # Return the reset flag status
        
            if self.scheduled_steps > 0:
                self.scheduled_steps -= 1
                break

            if self.is_running:
                break
        self.button_reset['state'] = tk.NORMAL
        return

    def update_canvas(self):
        self.canvas.delete("all")
        for x, row in enumerate(self.tilemap):
            for y, tile in enumerate(row):
                x1 = self.cnv_bndry + self.tile_size * x
                y1 = self.cnv_bndry + self.tile_size * y
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
        angle = Dir.getCode(self.hamster.getDir()) * -90 +90 # 0, 90, 180, 270 degrees
        self.current_hamster_image = ImageTk.PhotoImage(self.hamster_image.rotate(angle, expand=True))
        ham_pos = np.array(self.hamster.getPos(), dtype=float)
        ham_pos *= self.tile_size
        ham_pos += np.full((2), self.cnv_bndry, dtype=float)
        ham_pos += np.full((2), self.tile_size / 2, dtype=float)
        self.canvas.create_image(ham_pos[0], ham_pos[1], image=self.current_hamster_image)
        return


def create_map():
    map = np.array([
        [X, X, X, X, X, X, X, X],
        [X, 0,90, 0, 0, 0, 0, X],
        [X, 0, 0, 1, 0, X, 0, X],
        [X, 0, 0, 0, X, X, 0, X],
        [X, X, X, 0, 0, 0, 0, X],
        [X, 0, 0, 0, 0, 0, 0, X],
        [X, 0, 0, 0, 0, 0, 0, X],
        [X, 0, 0, 0, 0, 0, 0, X],
        [X, X, X, X, X, X, X, X]
        ], dtype=int)
    map = np.transpose(map)
    return map


def bhv_three_steps(hamster):
    hamster.turnLeft()
    for i in range(3):
        if hamster.isFree():
            hamster.forward()
    return


def bhv_follow_wall(hamster):
    # Example behavior: Move forward if free, else turn right
    while True:
        hamster.turnLeft()
        while not hamster.isFree():
            hamster.turnRight()
        hamster.forward()
    
        if hamster.countFloorFood() > 0:
            hamster.takeFood()
    return



def bhv_astar(hamster):
    FREE: int = 0
    OBST: int = -1

    pos = (0, 0)
    dest = (5, 7)
    todo = SortedList([pos])
    known = {pos: (FREE, (0, 0))}
    # todo = SortedList([(-1, 0), (0, -1), (0, 1), (1, 0)])
    while len(todo) > 0:
        ite_todo = todo.pop(0)
        # walk to todo
        # explore new neighbours -> add to todo if new
        hamster.getDir()
        for i in range(3):
            if hamster.isFree():
                pass

    return


def hamster_behavior(hamster):
    # TODO: WRITE YOUR CODE HERE!
    # To control the hamster, use functions "isFree(), forward(), turnRight(), turnLeft(), countMouthFood(), countFloorFood(), takeFood(), putFood()"

    # bhv_three_steps(hamster)
    bhv_follow_wall(hamster)
    bhv_astar(hamster)

    return


def main():
    root = tk.Tk()
    root.title("Hamster Tilemap Simulator")
    
    map = create_map()
    hamster = Hamster((1, 1), Dir.getVec(Dir.DOWN))
    simulator = TilemapSimulator(root, map, hamster, hamster_behavior)
    simulator.sim_main()
    return


# Main application
if __name__ == "__main__":
    main()


# TODO: Write your code into the function "hamster_behavior()" above!