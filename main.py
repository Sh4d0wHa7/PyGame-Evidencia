from pygame import *
import sys

init()
screen = display.set_mode((800,600))

while True:
    for e in event.get():
        if e.type == QUIT: sys.exit()
    screen.fill((255,255,255))
    display.flip()
