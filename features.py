import cv2
from numpy import *
from scipy import ndimage
from osgeo import gdal

def heightgrabber(igmarray, coords):
   latshift = sum(diff(igmarray[0][0])) / len(igmarray[0][0])
   longshift = sum(diff(igmarray[1][0])) / len(igmarray[1][0])

   for scanline in igmarray[0]:
      for lat in scanline:
         if (lat <= (coords[0]+latshift)) and (lat >= (coords[0]-longshift)):
            insidelat = lat

   for scanline in igmarray[1]:
      for long in scanline:
         if (long <= (coords[1]+longshift)) and (long >= (coords[1]-longshift)):
            insidelong = long
   insidelong = where(igmarray == insidelong)
   insidelat = where(igmarray == insidelat)

   height = igmarray[2][insidelat[1]][insidelat[2]]

   return height

def tiepointfilter(igmarray, keypointsarray, scanlinetiff):
   insideflightline=[]
   latshift = sum(diff(igmarray[0][0])) / len(igmarray[0][0])
   longshift = sum(diff(igmarray[1][0])) / len(igmarray[1][0])

   for point in keypointsarray:
      coords = pixelcoordinates(point.pt[0], point.pt[1], scanlinetiff)
      for scanline in igmarray[0]:
         for lat in scanline:
            if (lat <= (coords[0]+latshift)) and (lat >= (coords[0]-latshift)):
               insidelat = True
      for scanline in igmarray[1]:
         for long in scanline:
            if (long <= (coords[1]+longshift)) and (long >= (coords[1]-longshift)):
               insidelong = True

      if insidelong and insidelat:
         insideflightline.append(point)
   return insideflightline

def tiepointgenerator(scanline1, scanline2, igmarray):
   bf = cv2.BFMatcher()
   sli1 = ndimage.imread(scanline1)
   sli2 = ndimage.imread(scanline1)
   orb = cv2.ORB()
   #create keypoints
   slk1 = orb.detect(sli1)
   #filter to within the flightline object
   slk1 = tiepointfilter(igmarray, slk1)
   #compute descriptors
   slk1, sld1 = orb.compute(sli1, slk1)
   slk2, sld2 = orb.detectAndCompute(sli2, None)



   matches = bf.knnMatch(sld1, sld2)
   try:
      good = []
      for m, n in matches:
         if m.distance < 0.7 * n.distance:
            good.append(m)
   except Exception, e:
      print "something went horrifically wrong with bfmatcher :S"

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
         src_pts = float32([gcpkeypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
         dst_pts = float32([gcpkeypoints[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

         homography_matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

         #incase we need to use only inlier positive points
         #matchesMask = mask.ravel().tolist()

         h, w = gcpimg.shape

         #use the image shape to build a metric shape
         pts = float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)

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
   long = a * x + b * y + xoff
   lat = d * x + e * y + yoff
   return lat, long