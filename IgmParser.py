#!/usr/bin/env python
import gdal
import numpy as np
import math

def bilreader(bilfile):
   bildriver = gdal.GetDriverByName('ENVI')
   bildriver.Register()
   bil = gdal.Open(bilfile)

   bil = bil.ReadAsArray()

   return bil

def centerpixel(bilarray, point):
   bands, height, width = bilarray.shape

   if bands != 3:
      raise IOError, "this file has too many bands for an igm file"

   centerpx = (width / 2) - 1
   scanline=[]
   latlow = -1
   latscanlines = []
   for enum, scanline in enumerate(bilarray[0]):
      latidx = (np.abs(scanline - point[1])).argmin()
      if latidx != 951 and latidx != 0:
         latmin=scanline[latidx]
         # if abs(latmin-point[1]) <= abs(latlow-point[1]):
         latscanlines.append(enum)
         # latlow=latmin

   longlow = -1
   longscanlines=[]
   for enum, scanline in enumerate(bilarray[1]):
      longidx = (np.abs(scanline - point[0])).argmin()
      if longidx != 951 and longidx != 0:
         longmin = scanline[longidx]
         # if abs(longmin-point[0]) <= abs(longlow-point[0]):
         longscanlines.append(enum)
         # longlow=longmin


   scanlinenumber = None
   for latscan in latscanlines:
      for longscan in longscanlines:
         if longscan == latscan:
            scanlinenumber = longscan

   if scanlinenumber is not None:

      #gets the centre pixel location of any given scanline -1 so that it references correct array cent
      centerpx = (width / 2) - 1

      center = [bilarray[0][scanlinenumber][centerpx],
                bilarray[1][scanlinenumber][centerpx],
                bilarray[2][scanlinenumber][centerpx]]

      centerahead = [bilarray[0][scanlinenumber + 1][centerpx],
                     bilarray[1][scanlinenumber + 1][centerpx],
                     bilarray[2][scanlinenumber + 1][centerpx]]

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
   deltae = point2[0] - point1[0]
   deltan = point2[1] - point1[1]

   bearing = ((90 - math.atan2(deltan, deltae) / math.pi * 180) + 360) % 360

   return bearing