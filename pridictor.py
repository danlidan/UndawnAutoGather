import torch
import threading
import numpy as np
import ctypes
import mss
import time
from win32gui import FindWindow, GetWindowRect
import cv2

yolov5 = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5/best.pt', device='0')
yolov5.conf = 0.6
yolov5.iou = 0.4

COLORS = [
    (0, 0, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 255, 255),
    (255, 0, 255), (192, 192, 192), (128, 128, 128), (128, 0, 0),
    (128, 128, 0), (0, 128, 0), (128, 0, 128), (0, 128, 128), (0, 0, 128)]

LABELS = ['tree','stone']

img_src = np.zeros((1280,720,3),np.uint8)

def getScreenshot():
    id = FindWindow(None, "Toaa  ")
    x0,y0,x1,y1 = GetWindowRect(id)
    mtop,mbot = 30,50
    monitor = {"left": x0, "top": y0, "width": x1-x0, "height": y1-y0}
    img_src = np.array(mss.mss().grab(monitor))
    img_src = img_src[:,:,:3]
    img_src = img_src[mtop:-mbot]
    return img_src, [x0,y0,x1,y1,mtop,mbot]

def getMonitor():
    global img_src
    while True:
        last_time = time.time()
        img_src, _ = getScreenshot()
        #print("fps: {}".format(1 / (time.time() - last_time+0.000000001)))

def getDetection(img):
    bboxes = np.array(yolov5(img[:,:,::-1],size=1280).xyxy[0].cpu())
    return bboxes

def yolov5Detect():
    cv2.namedWindow("UndawnPridictor",cv2.WINDOW_NORMAL)
    cv2.resizeWindow("UndawnPridictor",960,540)
    cv2.moveWindow("UndawnPridictor",1560,0)
    global img_src
    while True:
        img = img_src.copy()
        bboxes = getDetection(img)
        img = drawBBox(img,bboxes)      
        cv2.imshow("UndawnPridictor", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break

def drawBBox(image, bboxes):
    for bbox in bboxes:
        conf = bbox[4]
        classID = int(bbox[5])
        if conf > yolov5.conf:
            x0,y0,x1,y1 = int(bbox[0]),int(bbox[1]),int(bbox[2]),int(bbox[3])
            color = [int(c) for c in COLORS[classID]]
            cv2.rectangle(image, (x0, y0), (x1, y1), color, 3)
            text = "{}: {:.2f}".format(LABELS[classID], conf)
            cv2.putText(image, text, (max(0,x0), max(0,y0-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return image

if __name__ == '__main__':
    ctypes.windll.user32.SetProcessDPIAware()
    t1 = threading.Thread(target=getMonitor,args=())
    t1.start()
    t2 = threading.Thread(target=yolov5Detect,args=())
    t2.start()