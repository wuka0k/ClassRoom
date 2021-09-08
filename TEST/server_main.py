# coding: utf-8
import socket
import threading
import struct
import cv2
import numpy

class Carame_Accept_Object:
    def __init__(self,S_addr_port=("",8880)):
        self.resolution = (640,480)
        self.img_fps = 15
        self.addr_port = S_addr_port
        self.Set_Socket(self.addr_port)

    def Set_Socket(self,S_addr_port):
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)#IPv4 流格式套接字

        self.server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)#通用套接字选项 允许重用本地地址和端口
        self.server.bind(S_addr_port)

        self.server.listen(5)#挂起最大连接数量

def check_option(object,client):
    info = struct.unpack('lhh',client.recv(8))
    if info[0] > 888:
        object.img_fps = int(info[0])-888
        object.resolution = list(object.resolution)
        object.resolution[0] = info[1]
        object.resolution[1] = info[2]
        object.resolution = tuple(object.resolution)
        return 1
    else:
        return 0

def RT_Image(object,client):
    if (check_option(object,client) == 0):
        return
    camera = cv2.VideoCapture(0)
    img_param = [int(cv2.IMWRITE_JPEG_QUALITY),object.img_fps]#img_fps压缩比率
    while(1):
        _,object.img = camera.read()#一帧的图片

        object.img = cv2.resize(object.img,object.resolution)#输出图片大小
        _,img_encode = cv2.imencode('.jpg',object.img,img_param)#网络带宽的限制 压缩成jpg格式#将图片格式转换(编码)成流数据，赋值到内存缓存中;主要用于图像数据格式的压缩，方便网络传输。

        img_code = numpy.array(img_encode)#生成数组
        object.img_data = img_code.tostring()
        try:
            client.send(
                struct.pack("lhh",len(object.img_data),object.resolution[0],object.resolution[1]) + object.img_data)#pack后就变成了C结构的二进制串
        except:
            camera.release()
            return

if __name__ == '__main__':
    camera = Carame_Accept_Object()
    while(1):
        client,_ = camera.server.accept()#接受一个客户端的连接请求，并返回一个新的套接字 连接地址
        clientThraed = threading.Thread(None,target=RT_Image,args=(camera,client,))
        clientThraed.start()



