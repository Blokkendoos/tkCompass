"""
compass_widget.py

Author:      J. van Oostrum
Date:        2021-09-20
Description: Animated compass widget
"""

import numpy as np
import tkinter as tk
import logging
import time
from PIL import Image, ImageTk
from math import pi, degrees, radians
from pubsub import pub

from damped_spring import DampedSpring


class Compass(tk.Frame):
    """
    The Compass class implements a (skeumorphic) liquid
    damped compass
    """
    wind_rose = {'N': 0.0,
                 'NNE': pi / 8,
                 'NE': pi / 4,
                 'ENE': pi*3 / 8,
                 'E': pi / 2,
                 'ESE': pi*5 / 8,
                 'SE': pi*3 / 4,
                 'SSE': pi*7 / 8,
                 'S': pi,
                 'SSW': pi*9 / 8,
                 'SW': pi*5 / 4,
                 'WSW': pi*11 / 8,
                 'W': pi*3 / 2,
                 'WNW': pi*13 / 8,
                 'NW': pi*7 / 4,
                 'NNW': pi*15 / 8}

    def __init__(self, root):
        super().__init__()
        self.root = root
        self.width = 300
        self.height = 300
        self.compass_offset = (60, 20)
        self.is_running = False

        self.angle_max = 2 * pi  # 360 degrees
        self.angle_min = -2 * pi
        self.angle_resolution = pi / 180  # minimum angle increment (rad)
        self.angle_step = 3
        self.angle_begin = 0.0
        self._angle = self.angle_begin  # rotation angle (rad)

        frame_rate = 24  # image/s
        self.animation_speed = int(1000 / frame_rate)  # frame interval (ms)
        self.animation_angle = self.angle_begin
        self.animation_max_time = 1.75  # seconds
        self.animation_start_time = 0.0
        self.animation_active = False
        self._animation_direction = 1

        # spring parameters
        self.k = 100  # spring constant
        self.m = 1  # mass
        self.k1_drag = 0.5  # drag
        self.v0 = 1.0  # initial velocity
        self.h0 = 0.0  # initial height
        self.dt = round(1 / frame_rate, 2)  # seconds

        self.canvas = tk.Canvas(root, width=self.width, height=self.height)
        self.canvas.configure(state=tk.DISABLED, bg='gray25')
        self.canvas.pack(fill=tk.BOTH, padx='2m', pady='2m')

        # https://stackoverflow.com/questions/15130670/pil-and-vectorbased-graphics
        img_bg = Image.open('./images/compass.png')
        bg = ImageTk.PhotoImage(img_bg)
        self.img_disc = Image.open('./images/compass_disc.png')
        disc = ImageTk.PhotoImage(self.img_disc)

        self.canvas.create_image(self.compass_offset, image=bg, anchor=tk.NW)
        self.canvas.image = bg  # keep object reference
        self.canvas.create_image(self.compass_offset, image=disc, anchor=tk.NW)
        self.canvas.disc = disc  # keep reference

        # pan and zoom stuff
        self.pan_x = 0
        self.pan_y = 0
        self.pan_x_start = 0
        self.pan_y_start = 0
        self.pan_distance = 0.0

        self.canvas.bind("<Button-3>", self.mouse_pan_start)
        self.canvas.bind("<B3-Motion>", self.mouse_pan)
        self.canvas.bind("<B3-ButtonRelease>", self.mouse_pan_stop)

        self.display_compass()

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        """
        Set the angle (radians)

        :param value: The angle in radians {-pi,pi} 0.0 pointing North
        """
        if not self.animation_active:
            self._angle = self.angle_limit(value)
            if self._angle > self.animation_angle:
                self._animation_direction = 1
            else:
                self._animation_direction = -1
            self.animate()

    @property
    def animation_direction(self):
        return self._animation_direction

    @animation_direction.setter
    def animation_direction(self, value):
        if not self.animation_active:
            self._animation_direction = value

    def angle_degrees(self, value):
        """ Set the angle (degrees) """
        angle = radians(value)
        self.angle = angle

    def angle_limit(self, angle):
        if angle < self.angle_min:
            angle = self.angle_min
        elif angle > self.angle_max:
            angle = self.angle_max
        return angle

    def cardinal_point(self, heading='N'):
        """ Move to the given wind direction """
        heading = heading.upper()
        if heading in self.wind_rose:
            self.angle = self.wind_rose[heading]
        else:
            logging.info("Invalid cardinal-point: {}".format(heading))

    def animate(self):
        self.animation_active = True
        pub.sendMessage('animation_begin')
        self.animation_start_time = time.time()
        self.animate_move()

    def animate_move(self):
        """ move to the target position """
        if self.animation_direction > 0 and self.animation_angle < self.angle:
            self.animation_angle += self.angle_step * self.angle_resolution
            self.display_compass()
            self.root.after(self.animation_speed, self.animate_move)
        elif (self.animation_direction < 0
              and self.animation_angle > self.angle):
            self.animation_angle -= self.angle_step * self.angle_resolution
            self.display_compass()
            self.root.after(self.animation_speed, self.animate_move)
        else:
            # moved the needle, now proceed with bounce
            self.spring = DampedSpring(dt=self.dt,
                                       k=self.k,
                                       m=self.m,
                                       k1_drag=self.k1_drag,
                                       h0=self.h0,
                                       v0=self.v0)
            self.root.after(self.animation_speed, self.animate_bounce)

    def animate_bounce(self):
        elapsed = time.time() - self.animation_start_time
        swing = self.spring.bounce()
        if elapsed < self.animation_max_time or abs(swing) > 0.001:
            if self.animation_direction > 0:
                self.animation_angle = self.angle + swing
            else:
                self.animation_angle = self.angle - swing
            self.display_compass()
            self.root.after(self.animation_speed, self.animate_bounce)
        else:
            self.animation_active = False
            self.animation_angle = self.angle   # animation under- or overshoot
            self.display_compass()
            pub.sendMessage('animation_end', duration=elapsed)

    def mouse_pan_start(self, event):
        if not self.animation_active:
            logging.debug("Pan start")
            self.pan_x_start = event.x
            self.pan_y_start = event.y
            self.pan_distance = 0.0

    def mouse_pan_stop(self, event):
        if not self.animation_active:
            logging.debug("Pan stop")
            dx = event.x - self.pan_x_start
            dy = event.y - self.pan_y_start
            diff = 10
            if abs(dx) > diff:
                self.animation_direction = -1 * np.sign(dx)
            elif abs(dy) > diff:
                self.animation_direction = np.sign(dy)
            self._angle = self.animation_angle
            self.animate()

    def mouse_pan(self, event):
        if not self.animation_active:
            dx = event.x - self.pan_x_start
            dy = event.y - self.pan_y_start
            diff = 5
            if abs(dx) > diff:
                self.pan_distance = (self.angle_step *
                                     self.angle_resolution * dx) / 4
            elif abs(dy) > diff:
                self.pan_distance = (self.angle_step *
                                     self.angle_resolution * dy) / 4
            self.animation_angle = self.pan_distance
            self.display_compass()

    def display_compass(self):
        self.canvas.delete(self.canvas.disc)

        # https://www.geeksforgeeks.org/how-to-rotate-an-image-using-python
        img_rot = self.img_disc.rotate(degrees(self.animation_angle))
        disc = ImageTk.PhotoImage(img_rot)

        self.canvas.create_image(self.compass_offset, image=disc, anchor=tk.NW)
        self.canvas.disc = disc  # keep a reference
