"""
compass_widget_test.py

Author:      J. van Oostrum
Date:        2021-09-20
Description: Animated widget demo
"""

import tkinter as tk
import logging
from math import pi
from pubsub import pub

from compass_widget import Compass


class Gui:
    def __init__(self, root):
        self.root = root
        self.width = 400
        self.height = 400
        self.is_running = False

        self.angle_max = pi  # 180 degrees
        self.angle = 0.0  # rotation angle (rad)
        self.angle_step = pi / 360  # angle increment steps (rad)
        self.speed = 10

        # constants
        self.k = tk.DoubleVar()  # spring constant
        self.m = tk.DoubleVar()  # mass
        self.k1_drag = tk.DoubleVar()  # drag
        self.v0 = tk.DoubleVar()  # initial velocity
        self.h0 = tk.DoubleVar()  # initial height

        self.animation_active = tk.BooleanVar()
        self.animation_duration = tk.DoubleVar()
        self.cardinal_point = tk.StringVar()
        self.cardinal_point.set('N')  # default North

        self.compass = Compass(self.root)
        self.compass.pack(side=tk.TOP)

        settings_frame = tk.Frame(root, width=self.width, padx='2m')
        settings_frame.pack(fill=tk.BOTH, side=tk.TOP)

        label0 = tk.Label(settings_frame,
                          text="(PgUp: rotate left, PgDn: rotate right)")
        label0.pack(fill=tk.NONE, side=tk.BOTTOM)

        # buttons
        b1 = tk.Button(settings_frame, text="Reposition",
                       command=self.reposition_click)
        b1.bind('<Return>', self.reposition_click)
        b1.pack(fill=tk.NONE, side=tk.LEFT)

        self.entry0 = tk.Entry(settings_frame,
                               width=4,
                               textvariable=self.cardinal_point)
        self.entry0.pack(fill=tk.NONE, side=tk.LEFT)
        self.entry0.bind('<Return>', self.reposition_click)

        self.text1 = tk.Text(settings_frame,
                             height=1, width='5',
                             state=tk.DISABLED)
        self.text1.pack(fill=tk.NONE, side=tk.RIGHT)
        label1 = tk.Label(settings_frame, text="Duration")
        label1.pack(fill=tk.NONE, side=tk.RIGHT)

        b2 = tk.Radiobutton(settings_frame,
                            variable=self.animation_active, value=True,
                            state=tk.DISABLED)
        b2.pack(fill=tk.NONE, side=tk.RIGHT)

        # constants control
        parameters_frame = tk.Frame(root, width=self.width,
                                    padx='2m', pady='2m')
        parameters_frame.pack(fill=tk.NONE, side=tk.BOTTOM)

        # sliders
        s1 = tk.Scale(parameters_frame,
                      from_=10.0, to=500.0,
                      label='k', length='35m',
                      showvalue=tk.TRUE, orient=tk.HORIZONTAL,
                      command=self.spring_constants,
                      variable=self.k)
        s1.set(100)
        s1.pack(fill=tk.NONE, side=tk.LEFT)

        s2 = tk.Scale(parameters_frame,
                      from_=1.0, to=50.0,
                      label='mass (kg)', length='35m',
                      showvalue=tk.TRUE, orient=tk.HORIZONTAL,
                      command=self.spring_constants,
                      variable=self.m)
        s2.set(2.0)
        s2.pack(fill=tk.NONE, side=tk.LEFT)

        parameters_frame2 = tk.Frame(root, width=self.width,
                                     padx='2m', pady='2m')
        parameters_frame2.pack(fill=tk.NONE, side=tk.BOTTOM)

        # https://stackoverflow.com/questions/25361926/tkinter-scale-and-floats-when-resolution-1
        s3 = tk.Scale(parameters_frame2,
                      from_=0.0, to=100.0, digits=4, resolution=0.0125,
                      label='k1_drag', length='35m',
                      showvalue=tk.TRUE, orient=tk.HORIZONTAL,
                      command=self.spring_constants,
                      variable=self.k1_drag)
        s3.set(10.0)
        s3.pack(fill=tk.NONE, side=tk.LEFT)

        s4 = tk.Scale(parameters_frame2,
                      from_=0.0, to=100.0, digits=4, resolution=0.0125,
                      label='v0', length='35m',
                      showvalue=tk.TRUE, orient=tk.HORIZONTAL,
                      command=self.spring_constants,
                      variable=self.v0)
        s4.set(1.0)
        s4.pack(fill=tk.NONE, side=tk.LEFT)

        s5 = tk.Scale(parameters_frame2,
                      from_=0.0, to=100.0, digits=4, resolution=0.0125,
                      label='h0', length='35m',
                      showvalue=tk.TRUE, orient=tk.HORIZONTAL,
                      command=self.spring_constants,
                      variable=self.h0)
        s5.set(0.0)
        s5.pack(fill=tk.NONE, side=tk.LEFT)

        root.bind('<Control-q>', self.quit_click)
        root.protocol("WM_DELETE_WINDOW", self.quit_click)

        root.bind('<Prior>', self.rotate_left)
        root.bind('<Next>', self.rotate_right)

        pub.subscribe(self.animation_begin, 'animation_begin')
        pub.subscribe(self.animation_end, 'animation_end')

    def animation_begin(self):
        self.text1.configure(state=tk.NORMAL)
        self.text1.delete(1.0, tk.END)
        self.text1.configure(state=tk.DISABLED)
        self.animation_active.set(False)

    def animation_end(self, duration):
        self.text1.configure(state=tk.NORMAL)
        self.text1.delete(1.0, tk.END)
        self.text1.insert(tk.END, duration)
        self.text1.configure(state=tk.DISABLED)
        self.animation_active.set(True)
        self.angle = self.compass.angle

    def reposition_click(self, event=None):
        self.compass.cardinal_point(self.cardinal_point.get())

    def spring_constants(self, event=None):
        """ Set the compass' spring parameters """
        self.compass.duration = self.animation_duration.get()
        self.compass.k = self.k.get()
        self.compass.m = self.m.get()
        self.compass.k1_drag = self.k1_drag.get()
        self.compass.h0 = self.h0.get()
        self.compass.v0 = self.v0.get()

    def rotate_left(self, event):
        self.angle += 6 * self.speed * self.angle_step
        logging.info("self.angle: {}".format(self.angle))
        self.compass.angle = self.angle

    def rotate_right(self, event):
        self.angle -= 6 * self.speed * self.angle_step
        logging.info("self.angle: {}".format(self.angle))
        self.compass.angle = self.angle

    def quit_click(self, event=None):
        if self.is_running:
            self.is_running = False
        self.root.destroy()


def run():
    root = tk.Tk()
    root.title("Animated widget")
    gui = Gui(root)
    root.mainloop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.WARNING)
    # logging.basicConfig(level=logging.DEBUG)
    run()
