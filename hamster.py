
from copy import copy, deepcopy
import math
from time import sleep, time

import os, sys
import tkinter as tk
from PIL import Image, ImageTk


# Constants for tile types
EMPTY = 0
X = 'X'
OBSTACLE = X


def game_over(text: str):
    print("Game Over - ", text)
    sys.exit()
    return

class Hamster:

    # dir_vecs: 0 = Up, 1 = Right, 2 = Down, 3 = Left
    dir_vecs = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    def __init__(self, x, y, mouth_food = 0, tilemap = None, reset_callback = lambda: None):
        self.x: int = x
        self.y: int = y
        self.mouth_food: int = mouth_food

        self.reset_callback: callable = reset_callback  # Callback for reset
        self.map: any = tilemap

        self.direction: int = 2  # Start facing Up
        return

    def bindSim(self, reset_callback, tilemap):
        self.reset_callback = reset_callback
        self.map = tilemap
        return

    def isFree(self):
        dx, dy = self.dir_vecs[self.direction]
        next_x, next_y = self.x + dx, self.y + dy
        return 0 <= next_x < len(self.map[0]) and 0 <= next_y < len(self.map) and self.map[next_y][next_x] != OBSTACLE
    
    def countMouthFood(self):
        if not isinstance(self.map[self.y][self.x], int):
            print("countMouthFood(): Something went wrong! Tile value is not an integer.")
            return 0
        return self.map[self.y][self.x]

    def countFloorFood(self):
        if not isinstance(self.map[self.y][self.x], int):
            print("countFloorFood(): Something went wrong! Tile value is not an integer.")
            return 0
        return self.map[self.y][self.x]

    def forward(self):
        if self.isFree():
            dx, dy = self.dir_vecs[self.direction]
            self.x += dx
            self.y += dy
        else:
            game_over("You crashed into an obstacle! Use isFree() to avoid this.")
        self.sim_step()
        return

    def turnLeft(self):
        self.direction = (self.direction - 1) % 4
        self.sim_step()
        return

    def turnRight(self):
        self.direction = (self.direction + 1) % 4
        self.sim_step()
        return

    def takeFood(self, num: int = 1):
        if num < 0:
            game_over("You tried to take a negative amount of food! Only positive values allowed.")
        if self.countFloorFood() < num:
            game_over("You tried to take more food than available! Use countFloorFood() to void this.")
        self.mouth_food += num
        self.map[self.y][self.x] -= num
        self.sim_step()
        return

    def putFood(self, num: int = 1):
        if num < 0:
            game_over("You tried to put down a negative amount of food! Only positive values allowed.")
        if self.mouth_food < num:
            game_over("You tried to put food that you do not have in your mouth! Use countMouthFood() to avoid this.")
        if not isinstance(self.map[self.y][self.x], int):
            print("putFood(): Something went wrong! Tile value is not an integer.")
            return
        self.mouth_food -= num
        self.map[self.y][self.x] += num
        self.sim_step()
        return

    def sim_step(self):
        self.reset_callback()
        return


class SimulationResetException(Exception):
    """Custom exception to handle simulation reset."""
    pass


class TilemapSimulator:

    def __init__(self, master, tilemap, hamster, cb_behavior):
        self.original_tilemap = deepcopy(tilemap)
        self.map = deepcopy(self.original_tilemap)
        self.original_hamster = deepcopy(hamster)

        self.cb_behavior = cb_behavior
        self.master = master

        self.tile_size = 60

        self.do_term = False
        self.do_reset = False  # Flag for reset
        self.is_running = False
        self.map_w = len(self.map[0])
        self.map_h = len(self.map)

        self.master.protocol("WM_DELETE_WINDOW", self.cb_close)

        # In the TilemapSimulator class __init__ method, modify the hamster image loading line:
        hamster_image_path = os.path.join(os.path.dirname(__file__), "hamster.png")
        self.hamster_image = Image.open(hamster_image_path).resize((int(self.tile_size / 2), int(self.tile_size / 2)), Image.LANCZOS)
        self.hamster_photo = ImageTk.PhotoImage(self.hamster_image)

        self.cnv_brd = self.tile_size / 2  # canvas border
        cnv_w = self.cnv_brd * 2 + self.tile_size * self.map_w
        cnv_h = self.cnv_brd * 2 + self.tile_size * self.map_h
        self.canvas = tk.Canvas(master, width=cnv_w, height=cnv_h)
        self.canvas.pack()

        self.button_play = tk.Button(master, width=10, command=self.cb_button_play)
        self.button_play.pack()
        # button text is set in callback
        for i in range(2):
            self.cb_button_play()

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
        self.map = deepcopy(self.original_tilemap)

        self.hamster = deepcopy(self.original_hamster)
        self.hamster.bindSim(self.cb_sim_step, self.map)

        self.scheduled_steps = 0
        self.is_running = False
        self.update_canvas()
        return

    def sim_main(self):
        while not self.do_term:
            self.init_sim()

            try:
                self.cb_sim_step()
                self.cb_behavior(self.hamster)
            except SimulationResetException:
                self.do_reset = False
        return

    def cb_button_play(self):
        self.is_running = not self.is_running
        button_text: str = "Play" if not self.is_running else "Pause"
        self.button_play.config(text=button_text)
        return
    
    def cb_button_step(self):
        # not incrementing, but setting to 1
        self.scheduled_steps = 1
        return

    def cb_button_reset(self):
        self.do_reset = True  # Set the reset flag
        self.is_running = False
        self.update_canvas()  # Update the canvas to reflect the reset state
        return
    
    def cb_close(self):
        # terminate cleanly
        self.do_term = True
        self.master.destroy()
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
        return

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
        self.canvas.create_image(hamster_x, hamster_y, image=self.current_hamster_image)
        return


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
        [X, X, X, X, X, X, X, X]
        ]


def hamster_behavior(hamster):
    # TODO: WRITE YOUR CODE HERE!
    # To control the hamster, use functions "isFree(), forward(), turnRight(), turnLeft(), countMouthFood(), countFloorFood(), takeFood(), putFood()"

    hamster.turnLeft()
    hamster.forward()
    hamster.forward()
    hamster.forward()


    """
    # Example behavior: Move forward if free, else turn right
    while True:
        hamster.turnLeft()
        while not hamster.isFree():
            hamster.turnRight()
        hamster.forward()
    
        if hamster.countFloorFood() > 0:
            hamster.takeFood()
    """

    return


def main():
    root = tk.Tk()
    root.title("Hamster Tilemap Simulator")
    
    map = create_map()
    hamster = Hamster(1, 1)
    simulator = TilemapSimulator(root, map, hamster, hamster_behavior)
    simulator.sim_main()
    return


# Main application
if __name__ == "__main__":
    main()


# TODO: Write your code into the function "hamster_behavior()" above!