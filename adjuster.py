#!/usr/bin/env python
import math
import numpy as np

import IgmParser

def intersect(point1, point2, point3, point4):
   """this 'should' work for a square or nearly square shape. If its not we might get an iffy return.
   For use with pixel coordinates to grab the lat long of a point

   Use with initial gcp image then rotate the resultant intersect through perspective transform"""
   c = point2[0] - point1[0]
   d = point2[1] - point1[1]

   x1 = point3[0] - point1[0]
   y1 = point3[1] - point1[1]

   x2 = point4[0] - point2[0]
   y2 = point4[1] - point2[1]

   mew = (d - ((c * y2) / x1) / (((y1 * x2) / x1) - y2))

   intersect = [mew * (x2 + point2[0]), mew * (y2 + point2[1])]

   return intersect

def calculator(scanlinetiff, sensorpoints, externalpoints, igmarray, altitude, groundcontrolpoints):
   #find heading angles
   headingvalues = []
   print "calculating heading..."
   for enum, point in enumerate(externalpoints):
      cont = True
      centerpx = None
      secondcentrepx = None
      if enum != (len(externalpoints) -1):
         sensorpoint = sensorpoints[enum]
         secondpoint = externalpoints[enum+1]
         secondsensorpoint = sensorpoints[enum+1]
         centerpx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
         secondcentrepx = IgmParser.centerpixel(igmarray, [secondpoint[1], secondpoint[2]])
         if (centerpx != None) and (secondcentrepx != None) and (float('nan') not in centerpx) and (float('nan') not in secondcentrepx):
            #first take all the points to the same centre axis by removing the centre pixel coordinates
            pointcentred = [point[1] - centerpx[0], point[2] - centerpx[1], point[3] - centerpx[2]]
            sensorpointcentred = [sensorpoint[1] - centerpx[0], sensorpoint[2] - centerpx[1], sensorpoint[3] - centerpx[2]]
            secondpointcentred =[secondpoint[1] - secondcentrepx[0], secondpoint[2] - secondcentrepx[1], secondpoint[3] - secondcentrepx[2]]
            secondsensorpointcentred =[secondsensorpoint[1] - secondcentrepx[0], secondsensorpoint[2] - secondcentrepx[1], secondsensorpoint[3] - secondcentrepx[2]]

            #find the intersect of those points
            intersectpoint = intersect(pointcentred, sensorpointcentred, secondpointcentred, secondsensorpointcentred)
            #need to return the intersectpoint to the scanline position and give it a z coordinate for the rest of the calculations
            intersectpoint = [intersectpoint[0] + centerpx[0],
                              intersectpoint[1] + centerpx[1],
                              centerpx[3]]

            #finally find the heading angle given the intersect point of the two points analysed
            try:
               heading = headingangle(intersectpoint, point[1:], sensorpoints[point[0] - 1][1:])
               if heading < 10:
                  headingvalues.append(heading)
            except Exception, e:
               print e


   headingvalues = [x for x in headingvalues if not math.isnan(x)]
   if len(headingvalues) > 1:
      headingstd = stdfiltering(headingvalues)
      heading = np.mean(headingstd)
   else:
      #we can't base heading on a single return
      heading = 0

   if heading != 0:
      print "adjusting points..."
      adjustedexternals=[]
      for enum, point in enumerate(externalpoints):
         centerpx = None
         centerpx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
         if centerpx:
            adjustedpoint = headingadjust(point[1:], centerpx, heading)
            adjustedexternals.append([point[0], adjustedpoint[0], adjustedpoint[1], adjustedpoint[2]])
      adjustedexternals=np.array(adjustedexternals)
   else:
      #if heading is 0 then there is no adjustment to be made
      adjustedexternals = externalpoints

   #need to convert heading to degrees to output, otherwise unusable
   heading  = math.degrees(heading)

   #find pitch and roll errors
   print "calculating pitch and roll..."
   pitchvalues = []
   rollvalues = []
   for enum, point in enumerate(adjustedexternals):
      centerpx = None
      centerpx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
      if centerpx != None:
         try:
            pitch, roll = pitchrolladjust(centerpx, point[1:], sensorpoints[int(point[0] - 1)][1:], altitude)
         except Exception, e:
            print e
            print type(point[0] - 1)
            pitch = float('nan')
            roll = float('nan')
         if math.isnan(pitch) and math.isnan(roll):
            continue
         else:
            if pitch < 10:
               pitchvalues.append(pitch)
            # print abs(pitch)
            if roll < 10:
               rollvalues.append(roll)
            # print roll
   print len(pitchvalues)
   print len(rollvalues)

   if len(pitchvalues) > 1 and len(rollvalues) > 1:
      #find average of pitch roll values
      print "filtering pitch and roll for outliers..."
      pitchstd = stdfiltering(np.array(pitchvalues))
      rollstd = stdfiltering(np.array(rollvalues))

      print "producing pitch and roll means"
      pitch = np.mean(pitchstd)
      roll = np.mean(rollstd)
      if (pitch > 10) or (roll > 10) or (heading > 10):
         print "adjustments seem excessively large (p %s r %s h %s), will ignore" % (pitch, roll, heading)
         raise ArithmeticError
      else:
         return pitch, roll, heading
   else:
      print "Warning, only one pitch or roll value successfully found for %s, " \
            "flightline disregarded but this will adversely effect the results" % (scanlinetiff)
      raise ArithmeticError


def stdfiltering(list, f=2):
   list=np.array(list)
   return list[(list - np.median(list)) < f * np.std(list)]

def meanstd(list):
   liststd = np.std(list)
   #remove heading angles above 2 std dev
   while not stdsmoothcheck(list, liststd):
      for num, item in enumerate(list):
         if item >= (liststd * 2):
            list.pop(num)
      liststd = np.std(list)
   listmean = sum(list) / len(list)
   return listmean, liststd

def stdsmoothcheck(list, liststd):
   smoothed = True
   for item in list:
      if item >= liststd:
         smoothed = False
   return smoothed

def headingangle(intersectpoint, truegcp, sensorgcp):
   #set xyz so that the calcs are a bit more sensible to read
   """
   generates heading angles from the center pixel for each

   :param centerpixel:
   :param truegcp:
   :param sensorgcp:
   :return:
   """
   x = 0
   y = 1
   z = 2
   #set for testing
   #centerpixel=array([x,y,z])
   #truegcp=array([x,y,z])
   #sensorgcp=array([x,y,z])
   #create the vector of the scanline direction
   sensorvect = [(sensorgcp[x] - intersectpoint[x]),
                 (sensorgcp[y] - intersectpoint[y]),
                 (sensorgcp[z] - intersectpoint[z])]
   # print "sensorvect"
   # print sensorvect

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(truegcp[x] - intersectpoint[x]),
              (truegcp[y] - intersectpoint[y]),
              (truegcp[z] - intersectpoint[z])]
   # print "gcpvect"
   # print gcpvect
   #create the magnitude (scalar) of the resultant vector
   gcpmag = math.sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)
   # print "gcpmag"
   # print gcpmag

   #calculation of the angle at which the gcp offsets the scanline
   #create a new pair of vectors based on what we already know
   u = gcpvect
   # print "u"
   # print u
   v = sensorvect
   # print "v"
   # print v

   #dotproduct
   dotproduct = (u[x] * v[x]) + (u[y] * v[y]) + (u[z] * v[z])
   # print "dotproduct"
   # print dotproduct

   #magnitude the results
   umag = math.sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))
   # print "umag"
   # print umag
   vmag = math.sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))
   # print "vmag"
   # print vmag
   #this gives us the angle that is less than (pi/2)/90
   theta = math.acos(dotproduct / (umag * vmag))
   if theta > (math.pi / 2):
      theta = math.pi - theta

   #to work out our pitch and roll adjustments we use beta and gamma respectively to draw an isosceles triangle
   #should take dem average from altitude to get true adjust

   return theta

#should have found the heading angle first
def headingadjust(point, centerpixel, angle):
   x = 0
   y = 1
   z = 2
   #make the center pixel the center of the axis

   gcp = [(point[x] - centerpixel[x]),
          (point[y] - centerpixel[y]),
          (point[z] - centerpixel[z])]

   xadjust = (gcp[x] * math.cos(angle)) + (gcp[y] * math.sin(angle))
   yadjust = (gcp[x] * -math.sin(angle)) + (gcp[y] * math.cos(angle))
   zadjust = gcp[z]
   adjustedgcp = [xadjust, yadjust, zadjust]

   #add the center pixel back on to bring it in to context
   adjustedpoint = [(adjustedgcp[x] + centerpixel[x]),
                  (adjustedgcp[y] + centerpixel[y]),
                  (adjustedgcp[z] + centerpixel[z])]
   return adjustedpoint

def pitchrolladjust(centerpixel, truegcp, sensorgcp, altitude):
   #set xyz so that the calcs are a bit more sensible to read
   x = 0
   y = 1
   z = 2
   # print "centerpixel"
   # print centerpixel
   # print "sensorgcp"
   # print sensorgcp
   # print "truegcp"
   # print truegcp
   #set for testing
   #centerpixel=array([x,y,z])
   #truegcp=array([x,y,z])
   #sensorgcp=array([x,y,z])
   #create the vector of the scanline direction
   sensorvect = [(sensorgcp[x] - centerpixel[x]),
                 (sensorgcp[y] - centerpixel[y]),
                 (sensorgcp[z] - centerpixel[z])]
   # print "sensorvect"
   # print sensorvect

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(truegcp[x] - sensorgcp[x]),
              (truegcp[y] - sensorgcp[y]),
              (truegcp[z] - sensorgcp[z])]
   # print "gcpvect"
   # print gcpvect
   #create the magnitude (scalar) of the resultant vector
   gcpmag = math.sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)

   # print "gcpmag"
   # print gcpmag

   #calculation of the angle at which the gcp offsets the scanline
   #create a new pair of vectors based on what we already know
   u = gcpvect
   # print "u"
   # print u
   v = sensorvect
   # print "v"
   # print v

   #dotproduct
   dotproduct = (u[x] * v[x]) + (u[y] * v[y]) + (u[z] * v[z])

   # print "dotproduct"
   # print dotproduct

   #magnitude the results
   umag = math.sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))

   # print "umag"
   vmag = math.sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))

   # print "vmag"
   # print vmag
   # this gives us the angle that is less than (pi/2)/90
   theta = math.acos(dotproduct / (umag * vmag))

   if theta > (math.pi / 2):
      theta = math.pi - theta

   #finally calculate the lengths of the outer edges Beta and Gamma
   beta = math.sin(theta) * gcpmag
   # print "beta"
   # print beta
   gamma = math.cos(theta) * gcpmag

   #to work out our pitch and roll adjustments we use beta and gamma respectively to draw an isosceles triangle
   #should take dem average from altitude to get true adjust
   altitude = altitude - ((centerpixel[z] + sensorgcp[z] + truegcp[z]) / 3)

   rolladjust = math.degrees(2 * (math.atan2((beta / 2), altitude)))
   pitchadjust = math.degrees(2 * (math.atan2((gamma / 2), altitude)))

   return pitchadjust, rolladjust