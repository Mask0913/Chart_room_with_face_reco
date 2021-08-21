import _tkinter
import tkinter as tk
from common.transmission.secure_channel import establish_secure_channel_to_server
from tkinter import messagebox
from common.message import MessageType
from pprint import pprint
from PIL import ImageDraw, ImageFont
from PIL import Image as PIL_image
from client.memory import current_user
import select
import client.util.socket_listener
import client.memory
from tkinter import *
import cv2
import dlib
import time
import numpy as np


class RegisterForm(tk.Frame):
    def cv2ImgAddText(self,img, text, left, top, textColor=(0, 255, 0), textSize=20):
        if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
            img = PIL_image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        fontText = ImageFont.truetype(
            "simsun.ttc", textSize, encoding="utf-8")
        draw.text((left, top), text, textColor, font=fontText)
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

    def get_face(self):
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor('model/shape_predictor_68_face_landmarks.dat')
        facerec = dlib.face_recognition_model_v1("model/dlib_face_recognition_resnet_model_v1.dat")
        tip = '你觉得当前人脸可以的话就按 q 保存当前的录入画面'
        cap = cv2.VideoCapture(0)
        now_time = time.time()
        while cap.isOpened():
            flag, im_rd = cap.read()
            dets = detector(im_rd, 1)
            if len(dets) != 0:
                biggest_face = dets[0]
                # 取占比最大的脸
                maxArea = 0
                for det in dets:
                    w = det.right() - det.left()
                    h = det.top() - det.bottom()
                    if w * h > maxArea:
                        biggest_face = det
                        maxArea = w * h
                cv2.rectangle(im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                              tuple([biggest_face.right(), biggest_face.bottom()]),
                              (255, 0, 0), 2)
                # 获取当前捕获到的图像的所有人脸的特征，存储到 features_cap_arr
                if (time.time() - now_time) > 2:
                    shape = predictor(im_rd, biggest_face)
                    features_cap = facerec.compute_face_descriptor(im_rd, shape)
                    now_time = time.time()
                im_rd = self.cv2ImgAddText(im_rd, tip, 0, 100, textColor=(0, 0, 255), textSize=23)
            cv2.imshow('get_face', im_rd)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        return features_cap
    def socket_listener(self, data):
        if data['type'] == MessageType.username_taken:
            messagebox.showerror('出错了', '用户名已被使用，请换一个')
            return

        if data['type'] == MessageType.register_successful:
            messagebox.showinfo('恭喜', '恭喜，注册成功，您的用户ID为：' + str(data['parameters']))
            self.remove_socket_listener_and_close()
            return

    def remove_socket_listener_and_close(self):
        client.util.socket_listener.remove_listener(self.socket_listener)
        self.master.destroy()

    def do_register(self):
        username = self.username.get()
        password = self.password.get()
        password_confirmation = self.password_confirmation.get()
        nickname = self.nickname.get()
        if not username:
            messagebox.showerror("出错了", "用户名不能为空")
            return
        if not password:
            messagebox.showerror("出错了", "密码不能为空")
            return
        if not nickname:
            messagebox.showerror("出错了", "昵称不能为空")
            return
        if password != password_confirmation:
            messagebox.showerror("出错了", "两次密码输入不一致")
            return
        face = self.get_face()
        face = np.array(face)
        face = face.tolist()
        face = str(face)
        self.sc.send(MessageType.register, [username, password, nickname,face])

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.sc = client.memory.sc


        master.resizable(width=False, height=False)
        master.geometry('190x140')
        self.master.title("注册账户")

        self.label_1 = Label(self, text="用户名")
        self.label_2 = Label(self, text="密码")
        self.label_3 = Label(self, text="确认密码")
        self.label_4 = Label(self, text="昵称")

        self.username = Entry(self)
        self.password = Entry(self, show="*")
        self.password_confirmation = Entry(self, show="*")
        self.nickname = Entry(self)

        self.label_1.grid(row=0, sticky=E)
        self.label_2.grid(row=1, sticky=E)
        self.label_3.grid(row=2, sticky=E)
        self.label_4.grid(row=3, sticky=E)

        self.username.grid(row=0, column=1, pady=(10, 6))
        self.password.grid(row=1, column=1, pady=(0, 6))
        self.password_confirmation.grid(row=2, column=1, pady=(0, 6))
        self.nickname.grid(row=3, column=1, pady=(0, 6))

        self.regbtn = Button(self, text="注册", command=self.do_register)
        self.regbtn.grid(row=4, column=0, columnspan=2)
        self.pack()

        self.sc = client.memory.sc
        client.util.socket_listener.add_listener(self.socket_listener)
        master.protocol("WM_DELETE_WINDOW", self.remove_socket_listener_and_close)
