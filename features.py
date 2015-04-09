import cv2

def pointgrabber(scanlinetiff, gcpoints):
   scanlineimg = cv2.imread(scanlinetiff)
   slgrey = cv2.cvtColor(scanlineimg, cv2.COLOR_BGR2GRAY)
   sift = cv2.SIFT()
   scanlinekeys = sift.detect(slgrey,None)
   for gcp in gcpoints:
       img = cv2.imread(gcp.imgpath)
       grey=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
       keypoints=sift.detect(grey,None)

       keypoints, descriptors = sift.compute(grey, keypoints)


def boxer(contours):
   for contour in contours:
      if 200<cv2.contourArea(contour)<5000:
         (x,y,w,h) = cv2.boundingRect(contour)
         cv2.rectangle(img,())