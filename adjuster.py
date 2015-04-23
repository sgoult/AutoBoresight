#!/usr/bin/env python
import math
import numpy as np

import IgmParser

def calculator(scanlinetiff, sensorpoints, externalpoints, igmarray, groundcontrolpoints):
   ALTITUDE = 2000
   #find heading angles
   headingvalues = []
   print "calculating heading..."
   for enum, point in enumerate(externalpoints):
      cont = True
      centerpx = None
      centerpx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
      if centerpx != None:
         heading = headingangle(centerpx, point[1:], sensorpoints[point[0] - 1][1:])
         headingvalues.append(heading)
   headingstd = stdfiltering(headingvalues)

   heading = np.mean(headingstd)

   print "adjusting points..."
   adjustedexternals=[]
   for enum, point in enumerate(externalpoints):
      centerpx = None
      centerpx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
      if centerpx:
         adjustedpoint = headingadjust(point[1:], centerpx, heading)
         adjustedexternals.append([point[0], adjustedpoint[0], adjustedpoint[1], adjustedpoint[2]])
   adjustedexternals=np.array(adjustedexternals)



   #find pitch and roll errors
   print "calculating pitch and roll..."
   pitchvalues = []
   rollvalues = []
   for enum, point in enumerate(externalpoints):
      centerpx = None
      centerpx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
      if centerpx != None:
         pitch, roll = pitchrolladjust(centerpx, point[1:], sensorpoints[point[0] - 1][1:], ALTITUDE)
         if math.isnan(pitch) and math.isnan(roll):
            continue
         else:
            pitchvalues.append(pitch)
            # print abs(pitch)
            rollvalues.append(roll)
            # print roll
   #find average of pitch roll values
   print "filtering pitch and roll for outliers..."
   pitchstd = stdfiltering(np.array(pitchvalues))
   rollstd = stdfiltering(np.array(rollvalues))

   print "producing pitch and roll means"
   pitch = np.mean(pitchstd)
   roll = np.mean(rollstd)
   return pitch, roll, heading

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

def headingangle(centerpixel, truegcp, sensorgcp):
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
   sensorvect = [(sensorgcp[x] - centerpixel[x]),
                 (sensorgcp[y] - centerpixel[y]),
                 (sensorgcp[z] - centerpixel[z])]
   # print "sensorvect"
   # print sensorvect

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(truegcp[x] - centerpixel[x]),
              (truegcp[y] - centerpixel[y]),
              (truegcp[z] - centerpixel[z])]
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
   #this is not right
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
   print "centerpixel"
   print centerpixel
   print "sensorgcp"
   print sensorgcp
   print "truegcp"
   print truegcp
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
   rolladjust = math.degrees(2 * (math.atan2((beta / 2), altitude)))
   pitchadjust = math.degrees(2 * (math.atan2((gamma / 2), altitude)))

   return pitchadjust, rolladjust