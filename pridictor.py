import torch
import threading
import numpy as np
import ctypes
import mss
import time
from win32gui import FindWindow, GetWindowRect
import cv2
import keyboard
from paddleocr import PaddleOCR

#ocr文本识别
ocr = PaddleOCR(use_angle_cls=False, lang="ch", show_log=False)
def getOcrText(img):
    result = ocr.ocr(img,cls=False)
    return result

yolov5 = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5/best.pt', device='0')
yolov5.conf = 0.51
yolov5.iou = 0.4

COLORS = [
    (0, 0, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 255, 255),
    (255, 0, 255), (192, 192, 192), (128, 128, 128), (128, 0, 0),
    (128, 128, 0), (0, 128, 0), (128, 0, 128), (0, 128, 128), (0, 0, 128)]

LABELS = ['tree','stone']

def getScreenshot():
    id = FindWindow(None, "Toaa  ")
    x0,y0,x1,y1 = GetWindowRect(id)
    mtop,mbot = 30,50
    monitor = {"left": x0, "top": y0, "width": x1-x0, "height": y1-y0}
    img_src = np.array(mss.mss().grab(monitor))
    img_src = img_src[:,:,:3]
    img_src = img_src[mtop:-mbot]
    return img_src, [x0,y0,x1,y1,mtop,mbot]

#预测目标
def getDetection(img):
    bboxes = np.array(yolov5(img[:,:,::-1],size=1280).xyxy[0].cpu())
    return bboxes

def drawBBox(image, bbox):
    if bbox.shape[0] == 0:
        return image
    conf = bbox[4]
    classID = int(bbox[5])
    if conf > yolov5.conf:
        x0,y0,x1,y1 = int(bbox[0]),int(bbox[1]),int(bbox[2]),int(bbox[3])
        color = [int(c) for c in COLORS[classID]]
        cv2.rectangle(image, (x0, y0), (x1, y1), color, 3)
        text = "{}: {:.2f}".format(LABELS[classID], conf)
        cv2.putText(image, text, (max(0,x0), max(0,y0-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return image

#优先矿石，再数目
def getLargestBox(bboxes):
    largest = -1
    bbox_largest = np.array([])
    for bbox in bboxes:
        if LABELS[int(bbox[5])] == 'tree' and bbox[4] > yolov5.conf:
            x0,y0,x1,y1 = int(bbox[0]),int(bbox[1]),int(bbox[2]),int(bbox[3])
            area = (x1-x0)*(y1-y0)
            if area > largest:
                largest = area
                bbox_largest = bbox
        elif LABELS[int(bbox[5])] == 'stone' and bbox[4] > yolov5.conf:
            bbox_largest = bbox
            break

    return bbox_largest

def getLabelExist(img):
    result = getOcrText(img)
    for re in result:
        for res in re:
            print(res)
            if res[1][0].find("级") != -1 or res[1][0].find("资") != -1 or res[1][0].find("源") != -1:
                return True
    return False 

if __name__ == '__main__':
    ctypes.windll.user32.SetProcessDPIAware()
    cv2.namedWindow("UndawnPridictor",cv2.WINDOW_NORMAL)
    cv2.resizeWindow("UndawnPridictor",960,540)
    cv2.moveWindow("UndawnPridictor",1560,0)
    
    img_src_width = 1280
    img_src_height = 720


    last_F = 0
    last_sight = 0
    last_sight_up = 0
    last_space = 0
    last_turn = time.time()
    sight_key = None
    sight_key_up = None

    while True:
        last_time = time.time()

        #定期跳一下摆脱障碍
        if last_time - last_space > 15:
            keyboard.press_and_release('space')
            last_space = last_time

        if last_time - last_F > 10:
            keyboard.press('w')
        else:
            keyboard.release('w')
            keyboard.press_and_release('f')

        img_src_origin, _ = getScreenshot()

        img_src = cv2.resize(img_src_origin, dsize=(img_src_width, img_src_height), interpolation=cv2.INTER_CUBIC)

        #定位靠近时ui的位置
        label = img_src[370:390, 890:950]
        cv2.imshow("label", label)

        #目标识别
        bboxes_pridict = getDetection(img_src)
        bbox_pridict = getLargestBox(bboxes_pridict)

        #瞄准目标
        if time.time() - last_sight > 0.05:
            if bbox_pridict.shape[0] != 0:
                x0,y0,x1,y1 = int(bbox_pridict[0]), int(bbox_pridict[1]), int(bbox_pridict[2]), int(bbox_pridict[3])
                cx = (x0 + x1) / 2
                if cx - 50 > img_src_width / 2:
                    sight_key = 'right'
                if cx + 50 < img_src_width / 2:
                    sight_key = 'left'
                if sight_key != None:
                    keyboard.release("right")
                    keyboard.release("left")
                    keyboard.press(sight_key)
                    last_sight = time.time()
                                   
        #文本识别
        cut = getLabelExist(label)
        if cut:
            last_F = time.time()
            keyboard.press_and_release('f')
    
        img_src = drawBBox(img_src.copy(), bbox_pridict)      
        cv2.imshow("UndawnPridictor", img_src)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break
        print("fps: {}".format(1 / (time.time() - last_time+0.000000001)))