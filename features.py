import cv2
from numpy import *

def pointgrabber(scanlinetiff, gcpoints):
   bruteforce = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
   scanlineimg = cv2.imread(scanlinetiff)
   slgrey = cv2.cvtColor(scanlineimg, cv2.COLOR_BGR2GRAY)
   orb = cv2.ORB()
   scanlinekeys = orb.detect(slgrey, None)
   scanlinekeys, scanlinedescriptors = orb.compute(slgrey, scanlinekeys)
   for gcp in gcpoints:
      gcpimg = cv2.imread(gcp.imgpath)
      gcpgrey = cv2.cvtColor(gcpimg,cv2.COLOR_BGR2GRAY)
      gcpkeypoints = orb.detect(gcpgrey,None)
      gcpkeypoints, gcpdescriptors = orb.compute(gcpgrey, gcpkeypoints)
      matches = bruteforce.match(gcpdescriptors, scanlinedescriptors)
      matches = sorted(matches, key = lambda x:x.distance)

      good = []
      for m, n in matches:
         if m.distance < 0.7 * n.distance:
            good.append(m)

      #assuming we have 10 good matches or more we can move on to the next stage
      if len(good) > 10:
         src_pts = float32([gcpkeypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
         dst_pts = float32([gcpkeypoints[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

         M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

         #incase we need to use only inlier positive points
         #matchesMask = mask.ravel().tolist()

         h, w = gcpimg.shape

         #use the image shape to build a metric shape
         pts = float32([ [0, 0], [0, h - 1],[w - 1, h - 1], [w - 1, 0] ]).reshape(-1, 1, 2)

         #we need to factor for distortion of the gcp image, so use cv2 perspective transform giving the final pixel points
         destinationpoints = cv2.perspectiveTransform(pts,M)
      else:
         print "Not enough matches are found - %d/%d" % (len(good),MIN_MATCH_COUNT)
         matchesMask = None

      intersect

def perp(a):
    b = empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

def intersect(a1, a2, b1, b2):
    da = a2 - a1
    db = b2 - b1
    dp = a1 - b1
    dap = perp(da)
    denom = dot(dap, db)
    num = dot(dap, dp)
    return (num / denom) * db + b1

def boxer(contours):
   for contour in contours:
      if 200<cv2.contourArea(contour)<5000:
         (x,y,w,h) = cv2.boundingRect(contour)
         cv2.rectangle(img,())