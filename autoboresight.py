#!/usr/bin/env python
import os, sys, argparse
import GcpParser
import features
import adjuster
import IgmParser
import numpy as np
import libgpstime
import read_sol_file


from osgeo import gdal


def altfind(hdrfile, navfile):
   for line in hdrfile:

      if "GPS Start Time" in line:
         start = line[27:]
      if "GPS Stop Time" in line:
         end = line[26:]
      if "acquisition" in line:
         day = line[37:]
   day, month, year = day.split('-')

   hour, minute, second = start.split(':')
   second = int(second[:2].replace('.',''))

   gpsstart = libgpstime.utc2gps_weeksec(int(year), int(month), int(day), int(hour), int(minute), int(second))
   hour, minute, second = end.split(':')
   second = int(second[:2].replace('.', ''))

   gpsstop = libgpstime.utc2gps_weeksec(int(year), int(month), int(day), int(hour), int(minute), int(second))
   trimmed_data=navfile[np.where(navfile['time'] > gpsstart)]
   trimmed_data=trimmed_data[np.where(trimmed_data['time'] < gpsstop)]

   altitude = np.mean(trimmed_data['alt'])
   return altitude

def autoboresight(scanlinefolder, gcpfolder, gcpcsv, igmfolder, navfile, output, hdrfolder):
   #associate gcps in the commandline ingest
   igmfiles = os.listdir(igmfolder)
   hdrfiles = os.listdir(hdrfolder)
   navfile = read_sol_file.readSol(navfile)
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
      flightlinename = flightline
      flightline = (scanlinefolder + '/' + flightline)
      flightlineheaderfile = open(hdrfolder + '/' + [hdrfile for hdrfile in hdrfiles if flightlinename[:6] in hdrfile and 'hdr' in hdrfile][0])
      flightlinealtitude = altfind(flightlineheaderfile, navfile)
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
                                              flightlinealtitude,
                                              groundcontrolpoints=True)
      else:
         gcpadjustments=None
      #this will always be run regardless if the gcps are there
      scanlineadjustments = []
      totalpoints = 0
      for scanline in os.listdir(scanlinefolder):
         #need to test if they have the same filename otherwise it would be bad
         if scanline not in flightlinename:
            print "%s being compared to %s" % (scanline, flightlinename)
            #first test for same altitude
            scanlineheaderfile = open(hdrfolder + '/' + [hdrfile for hdrfile in hdrfiles if scanline[:6] in hdrfile and 'hdr' in hdrfile][0])
            scanlinealtitude = altfind(scanlineheaderfile, navfile)


            if (scanlinealtitude >= flightlinealtitude - 100) and (scanlinealtitude <= flightlinealtitude + 100):
               print "altitudes matched at %s %s" % (scanlinealtitude, flightlinealtitude)
               #then test for overlap
               scanlineigmfile = [x for x in igmfiles if scanline[:6] in x and 'osng' in x and 'igm' in x and 'hdr' not in x][0]
               scanlineigmarray = IgmParser.bilreader(igmfolder + '/' + scanlineigmfile)
               scanline = scanlinefolder + '/' + scanline
               gdalscanline = gdal.Open(scanline)
               gdalflightline = gdal.Open(flightline)
               flightlinegeotrans = gdalscanline.GetGeoTransform()
               scanlinegeotrans = gdalscanline.GetGeoTransform()
               flightlinebounds = [flightlinegeotrans[0],
                                   flightlinegeotrans[3],
                                   flightlinegeotrans[0] + (flightlinegeotrans[1] * gdalflightline.RasterXSize),
                                   flightlinegeotrans[3] + (flightlinegeotrans[5] * gdalflightline.RasterYSize)]
               scanlinebounds = [flightlinegeotrans[0],
                                scanlinegeotrans[3],
                                scanlinegeotrans[0] + (scanlinegeotrans[1] * gdalscanline.RasterXSize),
                                scanlinegeotrans[3] + (scanlinegeotrans[5] * gdalscanline.RasterYSize)]

               overlap = [max(flightlinebounds[0], scanlinebounds[0]),
                          min(flightlinebounds[1], scanlinebounds[1]),
                          min(flightlinebounds[2], scanlinebounds[2]),
                          max(flightlinebounds[3], scanlinebounds[3])]

               if (overlap[2] < overlap[0]) or (overlap[1] < overlap[3]):
                  overlap = None

               if overlap != None:
                  print "overlap confirmed between %s and %s region is:" % (scanline, flightline)
                  print overlap
                  slk1, slk2, matches = features.tiepointgenerator(flightline, scanline, igmarray)
                  online=[]
                  offline=[]
                  i=1
                  totalpoints + len(matches)
                  #finally compare the images for key points
                  for match in matches:
                     #creates ordered lists of the matched points

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
                  try:
                     pit, rol, hed = adjuster.calculator(flightline, online, offline, igmarray, flightlinealtitude, groundcontrolpoints=False)
                     print pit, rol, hed
                     scanlineadjustments.append([np.float64(pit), np.float64(rol), np.float64(hed)])
                  except ArithmeticError:
                     continue
                  #except Exception, e:
                     #print e
                     #print "no match found between %s and %s" % (flightline, scanline)
               else:
                  print "no overlap between %s and %s" % (scanline, flightline)
            else:
               print "%s and %s flown at different altitudes (%s, %s), skipping to avoid result skew" % (flightlinename, scanline, flightlinealtitude, scanlinealtitude)
         else:
            continue

      p = 0
      r = 0
      h = 0

      if len(scanlineadjustments) != 0:
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
      else:
         continue

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
   if length > 1:
      p = p / length
      r = r / length
      h = h / length
   print "pitch"
   print p
   print "roll"
   print r
   print "heading"
   print h
   print "Calculated on %s points from %s flightlines" % (totalpoints, len(scanlinefolder))
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
   parser.add_argument('--lev1',
                       '-l',
                       help='level 1 folder with headers',
                       default="",
                       metavar="<folder>")
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

   if os.path.exists(commandline.lev1):
      hdrfolder = os.path.abspath(commandline.lev1)
   else:
      print "level 1 folder required, use -l or --lev1"
      exit(0)

   if commandline.gcps or commandline.gcpimages:
      if not commandline.gcps or not commandline.gcpimages:
         print "gcp csv or gcp images folder not present"
         exit(0)
      else:
         gcpimagesfolder = commandline.gcpimages
         gcpcsv = commandline.gcps

      boresight = autoboresight(gtifflist, gcpimagesfolder, gcpcsv, igmlist, navfile, None, hdrfolder)
   else:
      boresight = autoboresight(gtifflist, None, None, igmlist, navfile, None, hdrfolder)