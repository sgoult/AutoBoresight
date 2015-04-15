#!/usr/bin/env python
import gdal
import numpy as np

def bilreader(bilfile):
   bildriver = gdal.GetDriverByName('ENVI')
   bildriver.Register()
   bil = gdal.Open(bilfile)

   bil = bil.ReadAsArray()

   return bil

def centerpixel(bilarray, point):
   bands, height, width = bilarray.shape

   scanline=[]
   for loc, band in point, bands:
      scanline.append(np.where(bilarray == loc))

   if len(set(scanline)) <= 1:
      centerpx = width / 2

      center = []
      for i in bands:
         center[i] = bilarray[i][scanline[0][1]][centerpx]
   
   else:
      print "Point %s couldn't identify the scanline number" % point
