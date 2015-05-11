# AutoBoresight
Automated boresight function for push broom sensors. Required external
libraries:
Numpy
Scipy
Opencv 2.4.9 (64 bit)
read_sol_file.py
GDAL python

This program will take a folder of geotiffs, input geometry files,
level 1 header files and a navigation sol file. It identifies areas
for feature analysis, matches them across flightlines and estimates
the skew of their geo referencing, this is then presented as values
in degree format which can be used to correct sensor alignment caused
by physical mounting.

The files contained are released under the GPL v3 in accordance with
the source files the program utilises (read_sol_file.py). Read sol
file is a production of the Airborne Research Survey Facility and is
available here: https://github.com/pmlrsg/arsf_tools

Autoboresight was built with the intention of being used in the ARSF
environment using fedora 21, no guarantees are given that it will work
correctly on other operating systems and it is the users own
responsibility to verify its operations and outputs.