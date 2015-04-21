#!/usr/bin/env python
import math
import numpy as np

import IgmParser

def calculator(scanlinetiff, sensorpoints, externalpoints, igmarray, groundcontrolpoints):
   #find heading angles
   headingvalues = []
   for enum, point in enumerate(externalpoints):
      centrepx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
      heading = headingadjust(centrepx, point, sensorpoints[point[0]])
      headingvalues.append(heading)
   headingstd = stdfiltering(headingvalues)

   heading = np.mean(headingstd)

   adjustedexternals=[]
   for enum, point in enumerate(externalpoints):
      centrepx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
      adjustedpoint = headingadjust(point, centrepx, heading)
      adjustedexternals.append(adjustedpoint)



   #find pitch and roll errors
   pitchvalues = []
   rollvalues = []
   for enum, point in adjustedexternals:
      centrepx = IgmParser.centerpixel(igmarray, [point[1], point[2]])
      pitch, roll = pitchrolladjust(centrepx, point, sensorpoints[point[0]], 2000)
      pitchvalues.append(pitch)
      rollvalues.append(roll)
   #find average of pitch roll values
   pitchstd = stdfiltering(pitchvalues)
   rollstd = stdfiltering(rollvalues)

   pitch = np.mean(pitchstd)
   roll = np.mean(rollstd)

   return pitch, roll, heading

def stdfiltering(list, f=2):
   return list[(list - np.median(list)) < f * np.std(list)]

def meanstd(list):
   liststd = std(list)
   #remove heading angles above 2 std dev
   while not stdsmoothcheck(list, liststd):
      for num, item in enumerate(list):
         if item >= (liststd * 2):
            list.pop(num)
      liststd = std(list)
   listmean = sum(list) / len(list)
   return listmean, liststd

def stdsmoothcheck(list, liststd):
   smoothed = True
   for item in list:
      if item >= liststd:
         smoothed = False
   return smoothed

def headingangle(centrepixel, truegcp, sensorgcp):
   #set xyz so that the calcs are a bit more sensible to read
   """
   generates heading angles from the centre pixel for each

   :param centrepixel:
   :param truegcp:
   :param sensorgcp:
   :param altitude:
   :param demavg:
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
   sensorvect = [(sensorgcp[x] - centrepixel[x]),
                 (sensorgcp[y] - centrepixel[y]),
                 (sensorgcp[z] - centrepixel[z])]
   print "sensorvect"
   print sensorvect

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(truegcp[x] - centrepixel[x]),
              (truegcp[y] - centrepixel[y]),
              (truegcp[z] - centrepixel[z])]
   print "gcpvect"
   print gcpvect
   #create the magnitude (scalar) of the resultant vector
   gcpmag = math.sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)
   print "gcpmag"
   print gcpmag

   #calculation of the angle at which the gcp offsets the scanline
   #create a new pair of vectors based on what we already know
   u = gcpvect
   print "u"
   print u
   v = sensorvect
   print "v"
   print v

   #dotproduct
   dotproduct = (u[x] * v[x]) + (u[y] * v[y]) + (u[z] * v[z])
   print "dotproduct"
   print dotproduct

   #magnitude the results
   umag = math.sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))
   print "umag"
   print umag
   vmag = math.sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))
   print "vmag"
   print vmag
   #this gives us the angle that is less than (pi/2)/90
   theta = math.acos(dotproduct / (umag * vmag))
   print "theta"
   print theta

   #to work out our pitch and roll adjustments we use beta and gamma respectively to draw an isosceles triangle
   #should take dem average from altitude to get true adjust

   return theta

#should have found the heading angle first
def headingadjust(truegcp, centrepixel, angle):
   #this is not right
   x = 0
   y = 1
   z = 2

   #make the centre pixel the centre of the axis
   gcp = [(truegcp[x] - centrepixel[x]),
          (truegcp[y] - centrepixel[y]),
          (truegcp[z] - centrepixel[z])]

   xadjust = (gcp[x] * math.cos(angle)) + (gcp[y] * math.sin(angle))
   yadjust = (gcp[x] * -math.sin(angle)) + (gcp[y] * math.cos(angle))
   zadjust = gcp[z]
   adjustedgcp = [xadjust, yadjust, zadjust]

   #add the centre pixel back on to bring it in to context
   adjustedgcp = [(adjustedgcp[x] + centrepixel[x]),
                  (adjustedgcp[y] + centrepixel[y]),
                  (adjustedgcp[z] + centrepixel[z])]
   return adjustedgcp

def pitchrolladjust(centrepixel, truegcp, sensorgcp, altitude):
   #set xyz so that the calcs are a bit more sensible to read
   x = 0
   y = 1
   z = 2

   #set for testing
   #centerpixel=array([x,y,z])
   #truegcp=array([x,y,z])
   #sensorgcp=array([x,y,z])

   #create the vector of the scanline direction
   sensorvect = [(sensorgcp[x] - centrepixel[x]),
                 (sensorgcp[y] - centrepixel[y]),
                 (sensorgcp[z] - centrepixel[z])]
   print "sensorvect"
   print sensorvect

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(truegcp[x] - sensorgcp[x]),
              (truegcp[y] - sensorgcp[y]),
              (truegcp[z] - sensorgcp[z])]
   print "gcpvect"
   print gcpvect
   #create the magnitude (scalar) of the resultant vector
   gcpmag = math.sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)
   print "gcpmag"
   print gcpmag

   #calculation of the angle at which the gcp offsets the scanline
   #create a new pair of vectors based on what we already know
   u = gcpvect
   print "u"
   print u
   v = sensorvect
   print "v"
   print v

   #dotproduct
   dotproduct = (u[x] * v[x]) + (u[y] * v[y]) + (u[z] * v[z])
   print "dotproduct"
   print dotproduct

   #magnitude the results
   umag = math.sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))
   print "umag"
   print umag
   vmag = math.sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))
   print "vmag"
   print vmag
   #this gives us the angle that is less than (pi/2)/90
   theta = math.acos(dotproduct / (umag * vmag))
   print "theta"
   print theta

   #finally calculate the lengths of the outer edges Beta and Gamma
   beta = math.sin(theta) * gcpmag
   print "beta"
   print beta
   gma = math.cos(theta) * gcpmag
   print "gma"
   print gma

   #to work out our pitch and roll adjustments we use beta and gamma respectively to draw an isosceles triangle
   #should take dem average from altitude to get true adjust
   rolladjust = 2 * (math.atan(beta / 2) / altitude)
   pitchadjust = 2 * (math.atan(gma / 2) / altitude)

   return pitchadjust, rolladjust