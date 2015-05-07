#!/usr/bin/env python
import math
import numpy as np

import igmparser

def intersect(point1, point2, point3, point4):
   """
   Function intersect

   Takes 4 points and returns their intersection (or infinity if no intersect)
   point1 and point3 should form one line and point 2 and point 4 should form another.

   :param point1:
   :param point2:
   :param point3:
   :param point4:
   :return intersect vector (x,y):
   """
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
   """
   Takes a geotiff of a flightline, points on the scanline (sensorpoints), external points an igm array and the average
   altitude of the flightline.
   Returns adjustments for sensor direction in pitch roll and heading averaged across all points.

   Errors if not enough values are found rather than return uncertain amounts.

   :param scanlinetiff:
   :param sensorpoints:
   :param externalpoints:
   :param igmarray:
   :param altitude:
   :param groundcontrolpoints:
   :return pitch, roll, heading:
   """
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
         centerpx = igmparser.centrePixel(igmarray, [point[1], point[2]])
         secondcentrepx = igmparser.centrePixel(igmarray, [secondpoint[1], secondpoint[2]])
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
               heading = headingAngle(intersectpoint, point[1:], sensorpoints[point[0] - 1][1:])
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
         centerpx = igmparser.centrePixel(igmarray, [point[1], point[2]])
         if centerpx:
            adjustedpoint = headingAdjust(point[1:], centerpx, heading)
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
      centerpx = igmparser.centrePixel(igmarray, [point[1], point[2]])
      if centerpx != None:
         try:
            pitch, roll = pitchRollAdjust(centerpx, point[1:], sensorpoints[int(point[0] - 1)][1:], altitude)
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

def headingAngle(intersectpoint, offsensorpoint, onsensorpoint):
   """
   Function headingAngle

   Takes the intersect point, a point on a scanline and a point off a
   scanline and produces a heading angle

   :param centerpixel:
   :param offsensorpoint:
   :param onsensorpoint:
   :return theta(heading):
   """

   #set xyz so that the calcs are a bit more sensible to read
   x = 0
   y = 1
   z = 2

   #create the vector of the scanline direction
   sensorvect = [(onsensorpoint[x] - intersectpoint[x]),
                 (onsensorpoint[y] - intersectpoint[y]),
                 (onsensorpoint[z] - intersectpoint[z])]

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(offsensorpoint[x] - intersectpoint[x]),
              (offsensorpoint[y] - intersectpoint[y]),
              (offsensorpoint[z] - intersectpoint[z])]

   #create the magnitude (scalar) of the resultant vector
   gcpmag = math.sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)

   #calculation of the angle at which the gcp offsets the scanline
   #create a new pair of vectors based on what we already know
   u = gcpvect

   v = sensorvect

   #dotproduct
   dotproduct = (u[x] * v[x]) + (u[y] * v[y]) + (u[z] * v[z])

   #magnitude the results
   umag = math.sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))
   vmag = math.sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))

   #this gives us the angle that is less than (pi/2)/90
   theta = math.acos(dotproduct / (umag * vmag))
   #we need to double check it is the angle we need (the smaller one)
   if theta > (math.pi / 2):
      theta = math.pi - theta

   return theta

def headingAdjust(point, centrepixel, angle):
   """
   Function headingAdjust
   
   takes a point, a centre pixel and an angle, rotates the point around the centrepixel 
   by the angle and returns the rotated point.
   
   :param point: 
   :param centrepixel: 
   :param angle: 
   :return:
   """
   x = 0
   y = 1
   z = 2
   #make the center pixel the center of the axis

   gcp = [(point[x] - centrepixel[x]),
          (point[y] - centrepixel[y]),
          (point[z] - centrepixel[z])]

   xadjust = (gcp[x] * math.cos(angle)) + (gcp[y] * math.sin(angle))
   yadjust = (gcp[x] * -math.sin(angle)) + (gcp[y] * math.cos(angle))
   zadjust = gcp[z]
   adjustedpoint = [xadjust, yadjust, zadjust]

   #add the center pixel back on to bring it in to context
   adjustedpoint = [(adjustedpoint[x] + centrepixel[x]),
                  (adjustedpoint[y] + centrepixel[y]),
                  (adjustedpoint[z] + centrepixel[z])]
   return adjustedpoint

def pitchRollAdjust(centrepixel, offscanlinepoint, onscanlinepoint, altitude):
   """
   Function pitchRollAdjust

   Takes a centrepixel, point on a scanline, point off a scanline and an altitude. Calculates distances
   between these points and projects degree adjustments to correct the distance.

   :param centrepixel:
   :param offscanlinepoint:
   :param onscanlinepoint:
   :param altitude:
   :return pitchadjust, rolladjust:
   """
   #set xyz so that the calcs are a bit more sensible to read
   x = 0
   y = 1
   z = 2

   #create the vector of the scanline direction
   sensorvect = [(onscanlinepoint[x] - centrepixel[x]),
                 (onscanlinepoint[y] - centrepixel[y]),
                 (onscanlinepoint[z] - centrepixel[z])]

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(offscanlinepoint[x] - onscanlinepoint[x]),
              (offscanlinepoint[y] - onscanlinepoint[y]),
              (offscanlinepoint[z] - onscanlinepoint[z])]

   #create the magnitude (scalar) of the resultant vector
   gcpmag = math.sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)

   #calculation of the angle at which the gcp offsets the scanline
   #create a new pair of vectors based on what we already know
   u = gcpvect
   v = sensorvect

   #dotproduct
   dotproduct = (u[x] * v[x]) + (u[y] * v[y]) + (u[z] * v[z])

   #magnitude the results
   umag = math.sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))
   vmag = math.sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))

   # this gives us the angle that is less than (pi/2)/90
   theta = math.acos(dotproduct / (umag * vmag))

   #double check it is the correct (smallest) value
   if theta > (math.pi / 2):
      theta = math.pi - theta

   #finally calculate the lengths of the outer edges Beta and Gamma
   beta = math.sin(theta) * gcpmag
   gamma = math.cos(theta) * gcpmag

   #to work out our pitch and roll adjustments we use beta and gamma respectively to draw an isosceles triangle
   #should take dem average from altitude to get true adjust
   altitude = altitude - ((centrepixel[z] + onscanlinepoint[z] + offscanlinepoint[z]) / 3)

   rolladjust = math.degrees(2 * (math.atan2((beta / 2), altitude)))
   pitchadjust = math.degrees(2 * (math.atan2((gamma / 2), altitude)))

   return pitchadjust, rolladjust