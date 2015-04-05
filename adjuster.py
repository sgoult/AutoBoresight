from math import *
from numpy import *

def headingangle(centrepixel, truegcp, sensorgcp, altitude, demavg):
   #set xyz so that the calcs are a bit more sensible to read
   x=0
   y=1
   z=2

   #set for testing
   #centerpixel=array([x,y,z])
   #truegcp=array([x,y,z])
   #sensorgcp=array([x,y,z])

   #create the vector of the scanline direction
   sensorvect = [(sensorgcp[x] - centrepixel[x]), (sensorgcp[y] - centrepixel[y]), (sensorgcp[z] - centrepixel[z])]
   print "sensorvect"
   print sensorvect

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(truegcp[x] - centrepixel[x]), (truegcp[y] - centrepixel[y]), (truegcp[z] - centrepixel[z])]
   print "gcpvect"
   print gcpvect
   #create the magnitude (scalar) of the resultant vector
   gcpmag = sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)
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
   umag = sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))
   print "umag"
   print umag
   vmag = sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))
   print "vmag"
   print vmag
   #this gives us the angle that is less than (pi/2)/90
   theta = acos(dotproduct / (umag * vmag))
   print "theta"
   print theta

   #to work out our pitch and roll adjustments we use beta and gamma respectively to draw an isosceles triangle
   #should take dem average from altitude to get true adjust

   return theta

#should have found the heading angle first
def headingAdjust(truegcp, centrepixel, angle):
   #this is not right
   x = 0
   y = 1
   z = 2

   #make the centre pixel the centre pixel the centre of the axis
   gcp = [(truegcp[x] - centrepixel[x]), (truegcp[y] - centrepixel[y]), (truegcp[z] - centrepixel[z])]

   xadjust=(gcp[x]*cos(angle))+(gcp[y]*sin(angle))
   yadjust=(gcp[x]*-sin(angle))+(gcp[y]*cos(angle))
   zadjust=gcp[z]
   adjustedgcp=[xadjust,yadjust,zadjust]

   #add the centre pixel back on to bring it in to context
   adjustedgcp = [(adjustedgcp[x] + centrepixel[x]), (adjustedgcp[y] + centrepixel[y]), (adjustedgcp[z] + centrepixel[z])]
   return adjustedgcp

def pitchrolladjust(centrepixel, truegcp, sensorgcp, altitude, demavg):
   #set xyz so that the calcs are a bit more sensible to read
   x=0
   y=1
   z=2

   #set for testing
   #centerpixel=array([x,y,z])
   #truegcp=array([x,y,z])
   #sensorgcp=array([x,y,z])

   #create the vector of the scanline direction
   sensorvect = [(sensorgcp[x] - centrepixel[x]), (sensorgcp[y] - centrepixel[y]), (sensorgcp[z] - centrepixel[z])]
   print "sensorvect"
   print sensorvect

   #create the vector of the scanline direction

   #create the vector of the ground control point from its position in sensor space
   gcpvect = [(truegcp[x] - sensorgcp[x]), (truegcp[y] - sensorgcp[y]), (truegcp[z] - sensorgcp[z])]
   print "gcpvect"
   print gcpvect
   #create the magnitude (scalar) of the resultant vector
   gcpmag = sqrt((gcpvect[x]) ** 2 + (gcpvect[y]) ** 2 + (gcpvect[z]) ** 2)
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
   umag = sqrt(((u[x]) ** 2) + ((u[y]) ** 2) + ((u[z]) ** 2))
   print "umag"
   print umag
   vmag = sqrt(((v[x]) ** 2) + ((v[y]) ** 2) + ((v[z]) ** 2))
   print "vmag"
   print vmag
   #this gives us the angle that is less than (pi/2)/90
   theta = acos(dotproduct / (umag * vmag))
   print "theta"
   print theta

   #finally calculate the lengths of the outer edges Beta and Gamma
   beta = sin(theta) * gcpmag
   print "beta"
   print beta
   gma = cos(theta) * gcpmag
   print "gma"
   print gma

   #to work out our pitch and roll adjustments we use beta and gamma respectively to draw an isosceles triangle
   #should take dem average from altitude to get true adjust
   rolladjust = 2 * (atan(beta / 2) / altitude)
   pitchadjust = 2 * (atan(gma / 2) / altitude)

   return pitchadjust, rolladjust