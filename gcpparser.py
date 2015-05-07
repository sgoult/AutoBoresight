#!/usr/bin/env python
import csv
import numpy
import os

def GcpGrabber(csvfile):
   """
   converts a gcp csv to an array of data

   :param csvfile:
   :return gcparray:
   """
   gcparray = numpy.genfromtxt(csvfile, delimiter=',', skip_header=2)
   #grabs a gcp file and returns it as a numpy array
   return gcparray

def GcpImageAssociator(gcparray, imageslocation):
   """
   associates gcp points with their respective image plates for matching

   :param gcparray:
   :param imageslocation:
   :return gcparray:
   """
   imagefiles = os.listdir(imageslocation)
   for gcp in gcparray:
      gcp.append(imagefiles[(gcp[0] - 1)])

   return gcparray
