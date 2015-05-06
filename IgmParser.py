#!/usr/bin/env python
import gdal
import numpy as np
import math

def bilReader(bilfile):
   """
   Function bilReader

   Takes a bil file and outputs a numpy array using gdal

   :param bilfile:
   :return numpy array:
   """
   bildriver = gdal.GetDriverByName('ENVI')
   bildriver.Register()
   bil = gdal.Open(bilfile)

   bil = bil.ReadAsArray()

   return bil

def centrePixel(bilarray, point):
   """
   Function centrePixel

   Takes a bilarray and point on a flightline to identify the scanline and centre pixel relevant to
   that point. Also returns the bearing of the flightline at that centre pixel

   :param bilarray:
   :param point:
   :return centrepixelvector:
   """
   bands, height, width = bilarray.shape

   #test if the array is an IGM file
   if bands != 3:
      raise IOError, "this file has too many bands for an igm file"

   centerpx = (width / 2) - 1
   scanline=[]
   latlow = -1
   scanlines = []
   for enum, scanline in enumerate(bilarray[0]):
      latidx = (np.abs(scanline - point[0])).argmin()
      if latidx != 951 and latidx != 0:
         latmin=scanline[latidx]
         longmin = abs(point[1] - bilarray[1][enum][latidx])
         if longmin < 6:
         # if abs(latmin-point[1]) <= abs(latlow-point[1]):
            scanlines.append([enum, longmin])

   minimum=10
   scanlinenumber = None
   for idx in scanlines:
      idxminimum = idx[1]
      if idxminimum < minimum:
         minimum = idxminimum
         scanlinenumber = idx[0]

   if scanlinenumber is not None:

      #gets the centre pixel location of any given scanline -1 so that it references correct array cent
      centerpx = (width / 2) - 1

      center = [bilarray[0][scanlinenumber][centerpx],
                bilarray[1][scanlinenumber][centerpx],
                bilarray[2][scanlinenumber][centerpx]]

      centerahead = [bilarray[0][scanlinenumber + 1][centerpx],
                     bilarray[1][scanlinenumber + 1][centerpx],
                     bilarray[2][scanlinenumber + 1][centerpx]]

      #this is also the best time to return the bearing for this area of the flightline
      if scanlinenumber > 0:
         centerbehind = [bilarray[0][scanlinenumber - 1][centerpx],
                         bilarray[1][scanlinenumber - 1][centerpx],
                         bilarray[2][scanlinenumber - 1][centerpx]]
         bearing1 = bearingEstimator(centerbehind, centerahead)
         bearing2 = bearingEstimator(center, centerahead)
         bearing3 = bearingEstimator(centerbehind, center)

         bearing = (bearing1 + bearing2 + bearing3) / 3

      else:
         bearing = bearingEstimator(center, centerahead)

      center.append(bearing)
      return center
   else:
      return None

def bearingEstimator(point1, point2):
   """
   Function bearingEstimator

   Takes two points and calculates the bearing (point1 being the origin) in degrees

   :param point1:
   :param point2:
   :return bearing:
   """
   deltae = point2[0] - point1[0]
   deltan = point2[1] - point1[1]

   bearing = ((90 - math.atan2(deltan, deltae) / math.pi * 180) + 360) % 360

   return bearing