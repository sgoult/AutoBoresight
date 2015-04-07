import os, sys, argparse


if __name__=='__main__':
   #Get the input arguments
   parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
   parser.add_argument('--gcps','-g', help='Input gcp file to read', default="", metavar="<csvfile>")
   parser.add_argument('--tiepoints', '-t', help='Input tiepoints file to read', default="", metavar="<csvfile>")
   parser.add_argument('--hyper', '-h', help='Hyperspectral folder with all three levels available', default="", metavar="<csvfile>")
   parser.add_argument('--output','-o', help='Output TXT file to write', default="", metavar="<txtfile>")
   commandline=parser.parse_args()