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
            if res[1][0].find("矿") != -1 or res[1][0].find("树") != -1:
                return True
    return False 

def keyBoardReleaseAll():
    keyboard.release("right")
    keyboard.release("left")
    keyboard.release("shift")
    keyboard.release('w')

if __name__ == '__main__':
    ctypes.windll.user32.SetProcessDPIAware()
    cv2.namedWindow("UndawnPridictor",cv2.WINDOW_NORMAL)
    cv2.resizeWindow("UndawnPridictor",960,540)
    cv2.moveWindow("UndawnPridictor",1560,0)
    
    img_src_width = 1280
    img_src_height = 720
    last_space = 0
    sight_key = None

    #采集相关
    cut = False #当前帧是否识别出要砍树
    cut_mode_time = 0 #进入砍树模式的时间
    cut_mode_last = 10


    #-----全局变量区-----
    img_src = np.array(0)
    lock = threading.Lock()
    #-------------------

    def threadGrabScreen():
        global img_src
        global lock
        while True:
            last_time = time.time()

            img_src_origin, _ = getScreenshot()
            lock.acquire()
            img_src = cv2.resize(img_src_origin, dsize=(img_src_width, img_src_height), interpolation=cv2.INTER_CUBIC)
            lock.release()
            print("fps grabscreen: {}".format(1 / (time.time() - last_time+0.000000001)))


    t1 = threading.Thread(target=threadGrabScreen, args=())
    t1.start()

    while True:
        if img_src.size == 1:
            continue

        last_time = time.time()

        #1. 识别出要砍树
        if cut and cut_mode_time == 0: #不在砍树模式则进入砍树模式
            keyBoardReleaseAll()
            cut_mode_time = last_time

        #2. 在砍树模式持续时间内，持续砍树
        if last_time - cut_mode_time < cut_mode_last: 
            keyboard.press("right")
            keyboard.press_and_release("f")
        else: 
            #结束砍树模式
            if cut_mode_time != 0:
                cut_mode_time = 0
                keyBoardReleaseAll()

            #目标识别
            lock.acquire()
            label = np.copy(img_src[370:390, 810:870])
            bboxes_pridict = getDetection(img_src)
            bbox_pridict = getLargestBox(bboxes_pridict)
            lock.release()

            #定期跳一下摆脱障碍
            if last_time - last_space > 5:
                keyboard.press_and_release('space')
                last_space = last_time

            #3. 存在目标，且目标的框框大于阈值，缓速前进
            if bbox_pridict.shape[0] != 0:
                x0,y0,x1,y1 = int(bbox_pridict[0]), int(bbox_pridict[1]), int(bbox_pridict[2]), int(bbox_pridict[3])

                #首先瞄准目标            
                cx = (x0 + x1) / 2
                if cx - 50 > img_src_width / 2:
                    sight_key = 'right'
                if cx + 50 < img_src_width / 2:
                    sight_key = 'left'
                if sight_key != None:
                    keyboard.release("right")
                    keyboard.release("left")
                    keyboard.press(sight_key)

                print(x1 - x0, y1 - y0)
                if x1 - x0 > 125 or y1 - y0 > 300:
                    keyboard.release("shift")
                    keyboard.press("w")
                    time.sleep(0.03)
                    keyboard.release("w")
                #4. 存在目标，但目标的框框小于阈值
                else:
                    keyboard.press("shift")
                    keyboard.press("w")
            else:
                #5. 不存在目标
                if sight_key != None:
                    keyboard.press(sight_key)
                keyboard.press("shift")
                keyboard.press("w")

        #判断是否要砍树
        cut = getLabelExist(label)
            
        img_src = drawBBox(img_src.copy(), bbox_pridict)      
        cv2.imshow("UndawnPridictor", img_src)

        if label.size != 1:
            cv2.imshow("label", label)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break
        print("fps yolo: {}".format(1 / (time.time() - last_time+0.000000001)))
