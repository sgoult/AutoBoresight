#!/usr/bin/env python
import csv
import numpy
import os

def GcpGrabber(csvfile):
   gcparray = numpy.genfromtxt(csvfile, delimiter=',', skip_header=2)
   #grabs a gcp file and returns it as a numpy array
   return gcparray

def GcpImageAssociator(gcparray, imageslocation):
   imagefiles = os.listdir(imageslocation)
   for gcp in gcparray:
      gcp.append(imagefiles[(gcp[0] - 1)])

   return gcparray
