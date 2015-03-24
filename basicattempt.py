import argparse
import numpy
import sys
import os
import read_sol_file as sol

def planepostion(navinf):
   position=[]
   position.extend(navinf.lat)
   position.extend(navinf.long)
   position.extend(navinf.altitude)
   position.extend(navinf.pitch)
   position.extend(navinf.roll)
   position.extend(navinf.heading)
   return position

def sensorinfo():
   info=[]
   info.extend(37.7)
   info.extend(0.037165)
   info.extend(1024)
   info.extend(512)
   return info

def fovcalc(position, sensor):
   #currently ignores leverarms
   alt=position[2]
   fov=sensor[0]
   triangle = fov / 2
   demheight=demavgheight()
   dembase


def lineintersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

def demavgheight(dem):
   #placeholder for a better calculation in the future
   return 220

def pitchrotator(pitch):



print line_intersection((A, B), (C, D))