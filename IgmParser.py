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
   scanline.append(np.where(bilarray == point))

   scanline=[]
   print scanline

   if len(set(scanline)) <= 1:
      #gets the centre pixel location of any given scanline -1 so that it references correct array cent
      centerpx = (width / 2) - 1

      center = [bilarray[0][scanline[0][1]][centerpx], bilarray[1][scanline[1][1]][centerpx], bilarray[2][scanline[2][1]][centerpx]]

      centerahead = [bilarray[0][scanline[0][1] + 1][centerpx],
                     bilarray[1][scanline[1][1] + 1][centerpx],
                     bilarray[2][scanline[2][1] + 1][centerpx]]

      if scanline[0][1] > 0:
         centerbehind = [bilarray[0][scanline[0][1] - 1][centerpx],
                         bilarray[1][scanline[1][1] - 1][centerpx],
                         bilarray[2][scanline[2][1] - 1][centerpx]]
         bearing1 = bearingEstimator(centerbehind, centerahead)
         bearing2 = bearingEstimator(center, centerahead)
         bearing3 = bearingEstimator(centerbehind, center)

         bearing = (bearing1 + bearing2 + bearing3) / 3

      else:
         bearing = bearingEstimator(center, centerahead)

      center.append(bearing)

      return center

   else:
      raise Exception, "Point %s couldn't identify the scanline number, one value was out of position with the others" % point


def bearingEstimator(point1, point2):
   deltae = point2[0] - point1[0]
   deltan = point2[1] - point1[1]

   bearing = ((90 - math.atan2(deltan, deltae) / math.pi * 180) + 360) % 360

   return bearing