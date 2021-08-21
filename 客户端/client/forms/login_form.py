import _tkinter
import tkinter as tk
from tkinter import messagebox
from common.message import MessageType
from pprint import pprint
import client.memory
from client.forms.register_form import RegisterForm
from client.forms.contacts_form import ContactsForm
import select
import _thread
from tkinter import *
from tkinter import Toplevel
import client.util.socket_listener
import cv2
import dlib
import numpy as np
from PIL import ImageDraw, ImageFont
from PIL import Image as PIL_image
import json

class LoginForm(tk.Frame):
    def return_euclidean_distance(self,feature_1, feature_2):
        feature_1 = np.array(feature_1)
        feature_2 = np.array(feature_2)
        feature_1 = np.around(feature_1, decimals=3)
        feature_2 = np.around(feature_2, decimals=3)
        dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
        if dist > 0.35:
            return "diff"
        else:
            return "same"

    def cv2ImgAddText(self,img, text, left, top, textColor=(0, 255, 0), textSize=20):
        if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
            img = PIL_image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        fontText = ImageFont.truetype(
            "simsun.ttc", textSize, encoding="utf-8")
        draw.text((left, top), text, textColor, font=fontText)
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

    def reco(self,your_face):
        cap = cv2.VideoCapture(0)
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor('model/shape_predictor_68_face_landmarks.dat')
        facerec = dlib.face_recognition_model_v1("model/dlib_face_recognition_resnet_model_v1.dat")
        tip = '如果无法识别，请按 q 退出'
        while cap.isOpened():
            flag, im_rd = cap.read()
            dets = detector(im_rd)
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
                shape = predictor(im_rd, biggest_face)
                features_cap = facerec.compute_face_descriptor(im_rd, shape)
                compare = self.return_euclidean_distance(features_cap, your_face)
                im_rd = self.cv2ImgAddText(im_rd, tip, 0, 100, textColor=(0, 0, 255), textSize=23)
                if compare == "same":  # 找到了相似脸
                    cap.release()
                    cv2.destroyAllWindows()
                    return True
            cv2.imshow('face_recoinition', im_rd)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        return False



    def remove_socket_listener_and_close(self):
        client.util.socket_listener.remove_listener(self.socket_listener)
        self.master.destroy()

    def destroy_window(self):
        client.memory.tk_root.destroy()

    def socket_listener(self, data):
        if data['type'] == MessageType.login_failed:
            messagebox.showerror('登入失败', '登入失败，请检查用户名密码')
            return

        if data['type'] == MessageType.login_successful:
            your_face = data['parameters'][1]
            your_face = json.loads(your_face)
            your_face = np.array(your_face)
            if not self.reco(your_face):
                messagebox.showerror('登入失败', '登入失败，人脸识别失败')
                return
            client.memory.current_user = data['parameters'][0]
            self.remove_socket_listener_and_close()

            contacts = Toplevel(client.memory.tk_root, takefocus=True)
            ContactsForm(contacts)

            return

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        master.resizable(width=False, height=False)
        master.geometry('300x100')
        self.label_1 = Label(self, text="用户名")
        self.label_2 = Label(self, text="密码")

        self.username = Entry(self)
        self.password = Entry(self, show="*")

        self.label_1.grid(row=0, sticky=E)
        self.label_2.grid(row=1, sticky=E)
        self.username.grid(row=0, column=1, pady=(10, 6))
        self.password.grid(row=1, column=1, pady=(0, 6))

        self.buttonframe = Frame(self)
        self.buttonframe.grid(row=2, column=0, columnspan=2, pady=(4, 6))

        self.logbtn = Button(self.buttonframe, text="登入", command=self.do_login)
        self.logbtn.grid(row=0, column=0)

        self.registerbtn = Button(self.buttonframe, text="注册", command=self.show_register)
        self.registerbtn.grid(row=0, column=1)

        self.pack()
        self.master.title("聊天室")

        self.sc = client.memory.sc
        # self.sc.send(MessageType.client_echo, 0)
        client.util.socket_listener.add_listener(self.socket_listener)

    def do_login(self):
        username = self.username.get()
        password = self.password.get()
        if not username:
            messagebox.showinfo("出错了", "用户名不能为空")
            return
        if not password:
            messagebox.showinfo("出错了", "密码不能为空")
            return

        self.sc.send(MessageType.login, [username, password])

    def show_register(self):
        register_form = Toplevel()
        RegisterForm(register_form)
