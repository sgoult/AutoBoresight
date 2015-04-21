import os, sys, argparse
import GcpParser
import features
import adjuster
import IgmParser

#cv2.imread works on geotiffs.
from osgeo import gdal

def autoboresight(scanlinefolder, gcpfolder, gcpcsv, igmfolder, navfile, output):
   #associate gcps in the commandline ingest
   if gcpcsv:
      gcparray = GcpParser.GcpGrabber(gcpcsv)
      gcparray = GcpParser.GcpImageAssociator(gcparray, gcpfolder)
   adjust = []
   for flightline in scanlinefolder:
      igmarray = IgmParser.bilreader(igmfolder[np.where()])
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

      scanlineadjustments = []
      for scanline in scanlinefolder:
         #need to test if they have the same filename otherwise it would be bad
         if scanline != flightline:
            try:
               slk1, slk2, matches = features.tiepointgenerator(flightline, scanline)
               online=[]
               offline=[]
               i=1
               for match in matches:
                  #creates ordered lists of the matched points
                  coords = features.pixelcoords(slk1[match.queryIdx], flightline)
                  coords = features.heightgrabber(igmarray, coords)
                  online.append(i, coords)
                  coords = features.pixelcoords(slk2[match.trainIdx], flightline)
                  coords = features.heightgrabber(igmarray, coords)
                  offline.append(i, coords)
                  i+=1
               scanlineadjustments.append(adjuster.calculator(flightline,
                                                              online,
                                                              offline,
                                                              igmarray,
                                                              groundcontrolpoints=False))
            except:
               print "no match found between %s and %s" % flightline, scanline

      p = 0
      r = 0
      h = 0
      for adjustment in scanlineadjustments:
         p + adjustment[0]
         r + adjustment[1]
         h + adjustment[2]

      length = len(scanlineadjustments)
      p = p / length
      r = r / length
      h = h / length

      if gcpadjustments:
         pgcp = (p + gcpadjustments[0]) / 2
         rgcp = (r + gcpadjustments[1]) / 2
         hgcp = (h + gcpadjustments[2]) / 2

         adjust.append([p, r, h, pgcp, rpgcp, hgcp])
      else:
         adjust.append([p,r,h])

   p = 0
   r = 0
   h = 0
   for a in adjust:
      p = p + a[0]
      r = r + a[1]
      h = h + a[2]
   length = len(adjust)
   p = p / length
   r = r / length
   h = h / length

   print p, r, h

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

   if os.path.exists(commandline.i):
      igmlist = os.listdir(commandline.i)
   else:
      print "igm folder required, use -i or --igmfolder"

   if os.path.exists(commandline.t):
      gtifflist = os.listdir(commandline.t)
   else:
      print "geotiff folder required, use -t or --geotiffs"

   if os.path.exists(commandline.n):
      navfile = commandline.n
   else:
      print "nav file required, use -n or --navfile"

   if commandline.g or commandline.a:
      if not commandline.g or not commandline.a:
         print "gcp csv or gcp images folder not present"
      else:
         gcpimagesfolder = commandline.a
         gcpcsv = commandline.g

      boresight = autoboresight(gtifflist, gcpimagesfolder, gcpcsv, igmlist, navfile, None)
   else:
      boresight = autoboresight(gtifflist, None, None, igmlist, navfile, None)

   print boresight