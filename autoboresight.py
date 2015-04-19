import os, sys, argparse
import GcpParser


def autoboresight(scanlinefolder, gcpfolder, gcpcsv, igmfolder, output):
   #associate gcps in the commandline ingest
   flightlines=[]
   for flightline in scanlinefolder:
      gcps = []#produce matches to gcps
      for gcp in gcps:
         #adjust
         #average values
         #output
      #produce matches to other flightlines
      points = []#filter matches for points outside the flightline area
      for point in points:
         #find the geo location of the point in sensor space for 1 flightline
         #find it for the other
         #adjust
      #average tiepoints
      #average tiepoints and gcps
      #append to scanline list
   #average between scanlines
   #output final values


if __name__=='__main__':
   #Get the input arguments
   parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
   parser.add_argument('--gcps',
                       '-g',
                       help='Input gcp file to read',
                       default="",
                       metavar="<csvfile>")
   parser.add_argument('--gcpimages',
                       '-a',
                       help='gcp image plates for location identification',
                       default="",
                       metavar="<folder>")
   parser.add_argument('--projectfolder',
                       '-p',
                       help='Main project folder for boresight analysis',
                       default="",
                       metavar="<folder>")
   parser.add_argument('--igmfolder',
                       '-i',
                       help='project igm file folder',
                       default="",
                       metavar="<folder>")
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