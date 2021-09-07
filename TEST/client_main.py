import datetime
import socket
import struct
import sys
import threading
import qrc_rc
import cv2
import numpy
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QMessageBox, QApplication)
from widget import Ui_Widget
from login import Ui_Login
from PyQt5.uic import loadUi

class MyLoginClass(QtWidgets.QDialog,Ui_Login):
    def __init__(self):
        super().__init__()
        self.resize(500, 500)
        self.move(400, 200)

        self.set_ui()
        self.setWindowTitle('登录窗口')

    def set_ui(self):
        loadUi('./login.ui', self)
        self.pushButton.clicked.connect(self.login_btn_hand)
        self.pushButton_2.clicked.connect(self.quit)


    def quit(self):
        sys.exit()

    def login_btn_hand(self):
        if self.lineEdit_user.text() == "hao" and self.lineEdit_pwd.text() == "123456":
            QMessageBox.about(self, '登陆成功', '欢迎使用QST智能安防系统！')

            self.mainwin = MyMainClass()

            self.mainwin.show()





class MyMainClass(QtWidgets.QDialog,Ui_Widget):
    def __init__(self,parent=None):
        super(MyMainClass, self).__init__(parent)

        self.setupUi(self)

        self.resolution = [640,480]
        # self.addr_port = ("10.205.253.126",8880)#老师树莓派
        self.addr_port = ("192.168.43.170", 8880)#自己树莓派
        # self.addr_port = ("10.205.253.217", 8880)#电脑摄像头
        self.src = 888 +15
        self.interval = 0
        self.img_fps = 100

        self.button_exit.clicked.connect(self.quit)
        self.button_open.clicked.connect(self.button2_clicked)
        self.button_local.clicked.connect(self.get_local)
        print('MyMainClass init finished')

    def quit(self):
        sys.exit()

    def get_local(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        self.local_ip.setText(hostname)
        self.local_port.setText(ip)


    def button2_clicked(self):
        print('ip',self.serverip.text())
        self.Socket_Connect()
        print('port',self.addr_port[1])
        self.Get_Data(self.interval)



    def showTime(self):
        time = QDateTime.currentDateTime()

        timeDisplay = time.toString("yyyy-MM-dd hh:mm:ss dddd")
        self.label1.setText(timeDisplay)

    def Set_socket(self):
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        self.client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

    def Socket_Connect(self):

        self.Set_socket()

        print('Error', self.client.connect_ex(self.addr_port))

        print("IP is %s:%d" % (self.addr_port[0], self.addr_port[1]))

    def Get_Data(self,interval):
        print('Get_Data')
        self.socket_client()
        self.showThread = threading.Thread(target=self.socket_client)
        self.showThread.start()

    def socket_client(self):
        print('socket_client')

        self.client.send(struct.pack('lhh',self.src,self.resolution[0],self.resolution[1]))#long short short 8，帧，宽，高
        width = self.label_7.width()
        height = self.label_7.height()
        while 1:
            print(self.client.getsockname())

            info = struct.unpack('lhh',self.client.recv(8))
            buf_size = info[0]
            if buf_size:
                try:
                    self.buf = b""
                    self.avg = None
                    while(buf_size):
                        print('buf_size:',buf_size)
                        temp_buf = self.client.recv(buf_size)#接收图片数据长度的string类型字符串
                        print('temp_buf:',len(temp_buf))
                        buf_size -= len(temp_buf)#减后为零，退出循环
                        self.buf += temp_buf
                        data = numpy.frombuffer(self.buf,dtype='uint8')#tostring方法会丢失原始数据中的类型信息（type）和维度信息（shape）
                        self.image = cv2.imdecode(data,1)#从指定的内存缓存中读取数据，并把数据转换(解码)成图像格式;主要用于从网络传输数据中恢复出图像。


                        filename = 'image.jpg'
                        cv2.imwrite(filename,self.image)#保存图片


                        openJpg = QPixmap(filename).scaled(width,height)#缩放图片
                        self.label_7.setPixmap(openJpg)#显示图片

                        clientThraed = threading.Thread(None, target=self.RT_Image())
                        clientThraed.start()


                except:
                    pass
                    print('except')
                finally:
                    if (cv2.waitKey(10) == 27):#ESC
                        self.client.close()
                        cv2.destroyWindow()
                        break
                    print('finally')

    def RT_Image(self):
        width1 = self.label_8.width()
        height1 = self.label_8.height()
        # opencv识别
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)  # 高斯模糊
        if self.avg is None:
            self.avg = gray

        # cv2.accumulateWeighted(gray, self.avg, 0.5)  # 该函数计算输入图像src和累加器dst的加权和，使dst成为帧序列的运行平均值
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(
            self.avg))  # 图像增强convertScaleAbs#两张图片进行对比，返回的结果代表他们的差异之处
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[
            1]  # 返回值retval：与参数thresh一致dst： 结果图像#0黑255白#图像二值化，将整个图像呈现出明显的只有黑和白的视觉效果
        thresh = cv2.dilate(thresh, None, iterations=2)  # 膨胀，白覆盖黑，曝光
        # 检测物体的轮廓
        contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)[
                              -2:]  # 单通道图像矩阵 只检测最外围轮廓 仅保存轮廓的拐点信息
        for c in contours:
            if cv2.contourArea(c) < 900:  # 轮廓的面积
                continue
            else:
                print('move')

                (x, y, w, h) = cv2.boundingRect(c)  # x,y左上点,w,h宽高,包覆此轮廓的最小正矩形
                cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 255, 0),
                              2)  # (x,y)左上点,(x+w,y+h)右下点,(0,255,0)颜色,2线条宽度,绘制一个矩形框
                text = "HaoBingQian WangLei HouYanSong LuMingZhen"
                cv2.putText(self.image, "zhi neng an fang", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (101, 67, 254), 2)  # (10,20)文本框左下角
                cv2.putText(self.image, "HaoBingQian WangLei", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (101, 67, 254), 2)  # (10,20)文本框左下角
                cv2.putText(self.image, "HouYanSong LuMingZhen", (10, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (101, 67, 254), 2)  # (10,20)文本框左下角
                cv2.putText(self.image, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                            (10, self.image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (18, 87, 220),
                            2)  # object.img.shape[0]高度，object.img.shape[1]宽度，object.img.shape[2]通道数

                now_time = datetime.datetime.now()
                alarm_filename = 'Alarm' + datetime.datetime.strftime(now_time, '%Y-%m-%d-%H-%M-%S') + '.jpg'
                cv2.imwrite('./Alarm/' + alarm_filename, self.image)
                filename='./Alarm/'+alarm_filename
                openJpg = QPixmap(filename).scaled(width1, height1)  # 缩放图片
                self.label_8.setPixmap(openJpg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyLoginClass()
    window.show()
    sys.exit(app.exec_())