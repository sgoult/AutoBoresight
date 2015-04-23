#!/usr/bin/env python
import os, sys, argparse
import GcpParser
import features
import adjuster
import IgmParser
import numpy as np

#cv2.imread works on geotiffs.
from osgeo import gdal

def autoboresight(scanlinefolder, gcpfolder, gcpcsv, igmfolder, navfile, output):
   #associate gcps in the commandline ingest
   igmfiles = os.listdir(igmfolder)
   #if we have a gcpcsv then do stuff
   if gcpcsv:
      gcparray = GcpParser.GcpGrabber(gcpcsv)
      gcparray = GcpParser.GcpImageAssociator(gcparray, gcpfolder)
      adjust = []
   else:
      gcparray = None
   adjust=[]
   for flightline in os.listdir(scanlinefolder):
      igmfile = [x for x in igmfiles if flightline[:9] in x and 'osng' in x and 'igm' in x and 'hdr' not in x][0]
      flightline = (scanlinefolder + '/' + flightline)
      igmarray = IgmParser.bilreader(igmfolder + '/' + igmfile)
      #produce matches to gcps
      if gcparray:
         scanlinegcps = features.gcpidentifier(flightline, gcparray)
         filteredgcps = []
         for gcp in scanlinegcps:
            gcp.append(features.heightgrabber(igmarray, [gcp[1], gcp[2]]))
            for actualgcp in gcparray:
               if gcp[0] == actualgcp[0]:
                  filteredgcps.append(actualgcp)
         gcpadjustments = adjuster.calculator(flightline,
                                              scanlinegcps,
                                              filteredgcps,
                                              igmarray,
                                              groundcontrolpoints=True)
      else:
         gcpadjustments=None
      #this will always be run regardless if the gcps are there
      scanlineadjustments = []
      for scanline in os.listdir(scanlinefolder):
         #need to test if they have the same filename otherwise it would be bad
         if scanline not in flightline:
            print "%s being compared to %s" % (scanline, flightline)
            scanlineigmfile = [x for x in igmfiles if scanline[:9] in x and 'osng' in x and 'igm' in x and 'hdr' not in x][0]
            scanlineigmarray = IgmParser.bilreader(igmfolder + '/' + scanlineigmfile)
            scanline = scanlinefolder + '/' + scanline
            #try:
            slk1, slk2, matches = features.tiepointgenerator(flightline, scanline, igmarray)
            online=[]
            offline=[]
            i=1
            for match in matches:
               #creates ordered lists of the matched points
               gdalscanline = gdal.Open(scanline)
               gdalflightline = gdal.Open(flightline)

               onlinecoords = features.pixelcoordinates(slk1[match.queryIdx].pt[0], slk1[match.queryIdx].pt[1], gdalflightline)
               # print "online"
               # print slk1[match.trainIdx].pt
               # print onlinecoords
               onlinecoordsheight = features.heightgrabber(igmarray, onlinecoords)
               online.append([i, onlinecoords[0], onlinecoords[1], onlinecoordsheight])

               offlinecoords = features.pixelcoordinates(slk2[match.trainIdx].pt[0], slk2[match.trainIdx].pt[1], gdalscanline)
               # print "offline"
               # print slk2[match.trainIdx].pt
               # print offlinecoords
               offlinecoordsheight = features.heightgrabber(scanlineigmarray, offlinecoords)
               offline.append([i, offlinecoords[0], offlinecoords[1], offlinecoordsheight])
               i+=1
            pit, rol, hed = adjuster.calculator(flightline, online, offline, igmarray, groundcontrolpoints=False)
            print pit, rol, hed
            scanlineadjustments.append([np.float64(pit), np.float64(rol), np.float64(hed)])
            #except Exception, e:
               #print e
               #print "no match found between %s and %s" % (flightline, scanline)
         else:
            continue

      p = 0
      r = 0
      h = 0

      for adjustment in scanlineadjustments:

         p = np.float64(p + adjustment[0])
         r = np.float64(r + adjustment[1])
         h = np.float64(h + adjustment[2])

      length = len(scanlineadjustments)
      p = np.float64(p / length)
      r = np.float64(r / length)
      h = np.float64(h / length)

      if gcpadjustments != None:
         pgcp = (pgcp + gcpadjustments[0]) / 2
         rgcp = (rgcp + gcpadjustments[1]) / 2
         hgcp = (hgcp + gcpadjustments[2]) / 2

         adjust.append([p, r, h, pgcp, rgcp, hgcp])
      else:
         adjust.append([p, r, h])

   p = 0
   r = 0
   h = 0
   print "Total scanline adjustments:"
   print len(adjust)
   for a in adjust:
      # print a[0]
      p = p + a[0]
      # print a[1]
      r = r + a[1]
      # print a[2]
      h = h + a[2]
   length = len(adjust)
   p = p / length
   r = r / length
   h = h / length
   print "pitch"
   print p
   print "roll"
   print r
   print "heading"
   print h
   return p, r, h

if __name__=='__main__':
   #Get the input arguments
   parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
   parser.add_argument('--gcps',
                       '-g',
                       help='Input gcp file to read',
                       default=None,
                       metavar="<csvfile>")
   parser.add_argument('--gcpimages',
                       '-a',
                       help='gcp image plates for location identification',
                       default=None,
                       metavar="<folder>")
   parser.add_argument('--igmfolder',
                       '-i',
                       help='project igm file folder',
                       default="",
                       metavar="<folder>")
   parser.add_argument('--navfile',
                       '-n',
                       help='project nav file (sol/sbet)',
                       default="",
                       metavar="<sol/sbet>")
   parser.add_argument('--geotiffs',
                       '-t',
                       help='geotiffs folder (can be in the same folder as mapped bils)',
                       default="",
                       metavar="<folder>")
   parser.add_argument('--output',
                       '-o',
                       help='Output TXT file to write',
                       default="",
                       metavar="<txtfile>")
   commandline=parser.parse_args()

   if os.path.exists(commandline.igmfolder):
      igmlist = os.path.abspath(commandline.igmfolder)
   else:
      print "igm folder required, use -i or --igmfolder"
      exit(0)

   if os.path.exists(commandline.geotiffs):
      gtifflist = os.path.abspath(commandline.geotiffs)
   else:
      print "geotiff folder required, use -t or --geotiffs"
      exit(0)

   if os.path.exists(commandline.navfile):
      navfile = os.path.abspath(commandline.navfile)
   else:
      print "nav file required, use -n or --navfile"
      exit(0)

   if commandline.gcps or commandline.gcpimages:
      if not commandline.gcps or not commandline.gcpimages:
         print "gcp csv or gcp images folder not present"
         exit(0)
      else:
         gcpimagesfolder = commandline.gcpimages
         gcpcsv = commandline.gcps

      boresight = autoboresight(gtifflist, gcpimagesfolder, gcpcsv, igmlist, navfile, None)
   else:
      boresight = autoboresight(gtifflist, None, None, igmlist, navfile, None)