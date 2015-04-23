#!/usr/bin/env python
import cv2
import numpy as np
from scipy import ndimage
from osgeo import gdal

def heightgrabber(igmarray, coords):
   latlow = -1
   latlowidx = 0
   for enum, scanline in enumerate(igmarray[0]):
      latidx = (np.abs(scanline - coords[0])).argmin()
      latmin=scanline[latidx]
      if abs(latmin-coords[0]) <= abs(latlow-coords[0]):
         latlow=latmin
         if latlow != -1:
            latlowidx = latidx
            latscanline = enum
   longlow = -1
   longlowidx=0
   for enum, scanline in enumerate(igmarray[1]):
      longidx = (np.abs(scanline - coords[1])).argmin()
      longmin=scanline[longidx]
      if abs(longmin-coords[1]) <= abs(longlow-coords[0]):
         longlow=longmin
         if longlow != 0:
            longlowidx=longidx
            longscanline=enum

   height = igmarray[2][longscanline][longlowidx]
   return height

def tiepointfilter(igmarray, keypointsarray, scanlinetiff):
   insideflightline=[]
   # latshift = np.sum(np.diff(igmarray[0][0])) / len(igmarray[0][0]) *10
   # longshift = np.sum(np.diff(igmarray[1][0])) / len(igmarray[1][0]) *1000
   # print longshift
   # print latshift

   insidelong = False
   insidelat = False
   for point in keypointsarray:
      coords = pixelcoordinates(point.pt[0], point.pt[1], scanlinetiff)
      for scanline in igmarray[0]:
         latmin = np.amin(scanline)
         latmax = np.amax(scanline)
         if latmin - 4 <= coords[0] and latmax + 4 >= coords[0]:
            insidelat = True


      for scanline in igmarray[1]:
         longmin = np.amin(scanline)
         longmax = np.amax(scanline)
         if longmin - 4 <= coords[1] and longmax + 4 >= coords[1]:
            insidelong = True

      if insidelat and insidelong:
         insideflightline.append(point)
   return insideflightline

def tiepointgenerator(scanline1, scanline2, igmarray):
   bf = cv2.BFMatcher()
   sli1 = cv2.imread(scanline1)
   sli2 = cv2.imread(scanline2)
   orb = cv2.ORB()
   #create keypoints
   slk1 = orb.detect(sli1)
   #filter to within the flightline object
   scanlinegdal = gdal.Open(scanline1)
   slk1 = tiepointfilter(igmarray, slk1, scanlinegdal)
   print "SLKS"
   print len(slk1)
   #compute descriptors
   slk1, sld1 = orb.compute(sli1, slk1)
   slk2, sld2 = orb.detectAndCompute(sli2, None)

   matches = bf.knnMatch(sld1, sld2, k=2)

   try:
      good = []
      for m, n in matches:
         if m.distance < 7 * n.distance:
            good.append(m)
   except Exception, e:
      print e
      print "something went horrifically wrong with bfmatcher :S"
   print "GOOD"
   print len(good)
   return slk1, slk2, good

def gcpidentifier(scanlinetiff, gcpoints):
   MIN_MATCH_COUNT = 10
   bf = cv2.BFMatcher()
   scanlineimg = ndimage.imread(scanlinetiff)
   # slgrey = cv2.cvtColor(scanlineimg, cv2.COLOR_BGR2GRAY)
   orb = cv2.ORB()
   scanlinekeys = orb.detect(scanlineimg, None)
   scanlinekeys, scanlinedescriptors = orb.compute(scanlineimg, scanlinekeys)
   gcpsonscanline = []
   for gcp in gcpoints:
      gcpimg = ndimage.imread(gcp[4])
      gcpgrey = cv2.cvtColor(gcpimg, cv2.COLOR_BGR2GRAY)
      gcpkeypoints = orb.detect(gcpgrey, None)
      gcpkeypoints, gcpdescriptors = orb.compute(gcpgrey, gcpkeypoints)
      matches = bf.knnMatch(gcpdescriptors, scanlinedescriptors, k=2)
      try:
         good = []
         for m, n in matches:
            if m.distance < 0.7 * n.distance:
               good.append(m)
      except Exception, e:
         print "something went horrifically wrong with bfmatcher :S"

      #assuming we have 10 good matches or more we can move on to the next stage
      if len(good) > 10:
         src_pts = np.float32([gcpkeypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
         dst_pts = np.float32([gcpkeypoints[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

         homography_matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

         #incase we need to use only inlier positive points
         #matchesMask = mask.ravel().tolist()

         h, w = gcpimg.shape

         #use the image shape to build a metric shape
         pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)

         #transform our image into the the new plane
         destinationpoints = cv2.perspectiveTransform(pts, homography_matrix)
      else:
         print "Not enough matches are found for gcp (number)- %s/%s" % (len(good), MIN_MATCH_COUNT)
         matchesMask = None

      gcpcentre = intersect(pts)
      gcploc = pixelcoordinates(gcpcentre[0], gcpcentre[1], scanlinetiff)
      gcpsonscanline.append([gcp[0], gcploc[0], gcploc[1]])

   return gcpsonscanline

def intersect(points):
  """this 'should' work for a square or nearly square shape. If its not we might get an iffy return.
  For use with pixel coordinates to grab the lat long of a point

  Use with initial gcp image then rotate the resultant intersect through perspective transform"""
  c = points[1][0][0] - points[0][0][0]
  d = points[1][0][1] - points[0][0][1]

  x1 = points[2][0][0] - points[0][0][0]
  y1 = points[2][0][1] - points[0][0][1]

  x2 = points[3][0][0] - points[1][0][0]
  y2 = points[3][0][1] - points[1][0][1]

  mew = (d - ((c * y2) / x1) / (((y1 * x2) / x1) - y2))

  intersect = [mew * (x2 + points[1][0][0]), mew * (y2 + points[1][0][1])]

  return intersect


def pixelcoordinates(x, y, scanlinetiff):
   xoff, a, b, yoff, d, e = scanlinetiff.GetGeoTransform()
   easting = a * x + b * y + xoff
   northing = d * x + e * y + yoff
   return easting, northing