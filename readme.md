1. grab_screen.py 收集图片，输出到input文件夹中
2. 拉取https://github.com/Cartucho/OpenLabeling，手动做数据集
3. 拉取https://github.com/ultralytics/yolov5。
   训练命令 python train.py --img 1280 --batch 1 --epochs 200 --data Undawn.yaml --weights yolov5s6.pt 
   