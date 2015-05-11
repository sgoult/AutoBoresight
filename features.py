#!/usr/bin/env python
import cv2
import numpy as np
import distancecalculator
from scipy import ndimage
from osgeo import gdal

def heightGrabber(igmarray, coords):
   """
   Function heightGrabber

   Takes an igm array (file) and set of coordinates then associates a
   height with the established location

   :param igmarray:
   :param coords:
   :return height:
   """
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

def tiePointFilter(igmarray, keypointsarray, scanlinetiff):
   """
   Function tiePointFilter

   Takes an igm array, set of keypoints and geotiff then filters points to ensure
   they are within the flightline area

   :param igmarray:
   :param keypointsarray:
   :param scanlinetiff:
   :return insideflightline(array):
   """
   insideflightline=[]

   insidelong = False
   insidelat = False
   for point in keypointsarray:
      coords = pixelCoordinates(point.pt[0], point.pt[1], scanlinetiff)
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

def tiePointGenerator(scanline1, scanline2, igmarray):
   """
   Function tiePointGenerator

   Generates matched keypoints given two input flightlines and an igm array

   :param scanline1:
   :param scanline2:
   :param igmarray:
   :return keypoints for flighline 1, keypoints for flightline 2, matches:
   """
   bf = cv2.BFMatcher()
   sli1 = cv2.imread(scanline1)
   sli2 = cv2.imread(scanline2)
   orb = cv2.ORB(nfeatures=2000)
   #create keypoints
   slk1 = orb.detect(sli1)
   #filter to within the flightline object
   scanlinegdal = gdal.Open(scanline1)
   slk1 = tiePointFilter(igmarray, slk1, scanlinegdal)
   print "Keypoints identified on the scanline"
   print len(slk1)
   #compute descriptors
   slk1, sld1 = orb.compute(sli1, slk1)
   slk2, sld2 = orb.detectAndCompute(sli2, None)

   matches = bf.knnMatch(sld1, sld2, k=2)

   try:
      good = []
      for m, n in matches:
         if m.distance < 0.9 * n.distance:
            good.append(m)
   except Exception, e:
      print e
      print "something went wrong with bfmatcher"

   destination_points = np.float32([slk1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
   source_points = np.float32([slk2[m.trainIdx].pt for m in good]).reshape(-1,1,2)

   matrix, mask = cv2.findHomography(source_points, destination_points, cv2.RANSAC, 5.0)

   matched_points = cv2.perspectiveTransform(source_points, matrix)

   slk1_filtered = []
   slk2_filtered = []
   for e, point in enumerate(matched_points):
      if (destination_points[e][0][0] + 100) > point[0][0] and (destination_points[e][0][0] - 100) < point[0][0]:
         if (destination_points[e][0][1] + 100) > point[0][1] and (destination_points[e][0][1] - 100) < point[0][0]:
            slk1_filtered.append(np.float32(slk1[e].pt))
            slk2_filtered.append(np.float32(point[0]))

   print "Keypoints to be taken forward as tiepoints"
   print len(slk1_filtered)
   return slk1_filtered, slk2_filtered

def gcpIdentifier(scanlinetiff, gcpoints):
   """
   Function gcpIdentifier

   Takes a flightline geotiff and gcppoints array with image locations appended,
   returns any valid gcp points on the flightline using image plates of gcp locations

   :param scanlinetiff:
   :param gcpoints:
   :return array of gcps on the scanline in vector format:
   """
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
            if m.distance < 0.8 * n.distance:
               good.append(m)
      except Exception, e:
         print "something went wrong with matching"

      #assuming we have 10 good matches or more we can move on to the next stage
      if len(good) > 10:
         src_pts = np.float32([gcpkeypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
         dst_pts = np.float32([scanlinekeys[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

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

      gcpcentre = distancecalculator.intersect(pts)
      gcploc = pixelCoordinates(gcpcentre[0], gcpcentre[1], scanlinetiff)
      gcpsonscanline.append([gcp[0], gcploc[0], gcploc[1]])

   return gcpsonscanline


def pixelCoordinates(x, y, scanlinetiff):
   """
   Function pixelCoordinates

   Takes x y coordinates of a pixel in a geotiff, uses gdal to convert them into a lat/long or eating/northing format

   :param x:
   :param y:
   :param scanlinetiff:
   :return easting, northing:
   """
   xoff, a, b, yoff, d, e = scanlinetiff.GetGeoTransform()
   easting = a * x + b * y + xoff
   northing = d * x + e * y + yoff
   return easting, northing