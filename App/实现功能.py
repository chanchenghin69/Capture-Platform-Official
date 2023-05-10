from PySide2.QtCore import Qt, QTimer, QFile, QEvent
from PySide2.QtGui import QCursor, QPixmap, QGuiApplication, QImage, QMouseEvent
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
import os ,cv2
from glob import glob
import numpy as np

w = [1, 0.5, 0.25, 0.125, 0.0625, 0]
sigma = 0.248

class Gaussian:
    def __init__(self,sigam,w):
        self.sigam = sigam
        self.w = w
        self.pyramid = []
        self.vcenter = []
        self.R = []
        self.T = []
        self.B = []
        self.levelground = []
        self.outputs = []

    def get_multi_resolution_pyramid(self, image):
        """
        计算多分辨率金字塔
        :return:
        """
        py = []
        py.append(image)
        self.pyramid.append(image)
        self.x, self.y = image.shape[1], image.shape[0]

        for i in range(5):
            blurred = cv2.GaussianBlur(py[-1], (3,3), sigmaX=self.sigam,sigmaY=self.sigam)

            downsampled = cv2.pyrDown(blurred)
            py.append(downsampled)

            self.pyramid.append(cv2.pyrUp(py[-1]))

        for i in range(6):
            self.pyramid[i] = cv2.resize(self.pyramid[i] , image.shape[:2][::-1])


        return

    def get_vc_R_T(self,vc):
        """
        获取视觉中心
        然后计算视角
        传递函数
        :return:
        """
        self.xc,self.yc = vc[0], vc[1]

        theta_value = np.empty((self.x,self.y))
        trans_funcs = np.empty((6,self.x,self.y))

        for i in range(self.x):
            for j in range(self.y):
                theta_value[i][j] = (((i - self.xc) ** 2 + (j - self.yc) ** 2) ** 0.5) / 7.5

        R_value = 2.5 / (2.5 + theta_value)

        self.R.append(R_value)

        for g in range(6):
            if g < 5:
                trans_funcs[g] = np.exp(-0.5 * (2 ** (g - 2) * R_value / self.sigam) ** 2)
            else:
                trans_funcs[g] = 0

        self.T.append(trans_funcs)

    def get_blending_func(self):
        """
        计算混合函数
        :return:
        """
        R = self.R[0]
        T = self.T[0]

        level_ground_value = np.empty((self.x,self.y))
        B_value = np.empty((6,self.x,self.y))

        for k in range(5,-1,-1):
            for i in range(self.x):
                for j in range(self.y):
                    if R[i][j] <= self.w[k]:
                        B_value[k][i][j] = 0
                        continue

                    if self.w[k - 1] >= R[i][j] >= self.w[k]:
                        level_ground_value[i][j] = k
                        B_value[k][i][j] = (0.5 - T[k][i][j]) / (T[k-1][i][j] - T[k][i][j])
                        if B_value[k][i][j] <= 0:
                            B_value[k][i][j] = 0
                        continue

                    if R[i][j] >= self.w[k-1]:
                        level_ground_value[i][j] = k - 1
                        B_value[k][i][j] = 1
                        continue

        self.B.append(B_value)
        self.levelground.append(level_ground_value)

        return

    def get_blending_image(self):
        """
        计算混合图片
        :return:
        """
        B = np.transpose(self.B[0],(0,2,1))
        level = np.transpose(self.levelground[0],(1,0))
        O_value = np.empty((self.y,self.x,3))

        up = self.pyramid

        for i in range(self.y):
            for j in range(self.x):
                for l in range(3):
                    O_value[i][j][l] += B[int(level[i][j])][i][j] * up[int(level[i][j])][i][j][l] + (1 - B[int(level[i][j])][i][j]) * up[int(level[i][j])-1][i][j][l]

        O_value = np.array(O_value, dtype='uint8')

        self.outputs.append(O_value)

        return


class MainWindow:
    def __init__(self):
        #从文件中加载UI定义
        qfile_mainwindow = QFile("ui/MainWindow.ui")
        qfile_mainwindow.open(QFile.ReadOnly)
        qfile_mainwindow.close()

        self.mainwindow = QUiLoader().load(qfile_mainwindow)
        self.mainwindow.start_button.clicked.connect(self.start_button_clicked)

    def start_button_clicked(self):
        # 实例化另外一个窗口
        self.fullscreenimagewindow = FullscreenImageWindow()
        # 显示新窗口
        self.fullscreenimagewindow.show()
        # 关闭自己
        self.mainwindow.close()


class FullscreenImageWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始时在窗口中心放置一个空白的QLabel
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)

        self.setWindowState(Qt.WindowFullScreen)  # 设置窗口为全屏模式
        self.setCursorPosition()  # 将鼠标放置于屏幕中央
        self.photo_paths = self.load_images_paths("image_file")  # 读取照片
        self.mouse_position = QCursor.pos()  # 鼠标的坐标

        # 检测鼠标位置是否发生改变，若改变则根据变化后的鼠标的位置来更新图片
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_mouse_position)
        self.timer.start(10)

        # 初始化显示的图片和计时器
        self.current_image_index = 0
        self.show_image(self.photo_paths[self.current_image_index])
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.switch_image)
        self.timer.start(8000)

    def setCursorPosition(self):
        # 将鼠标放置于屏幕中央
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        center = screen_geometry.center()
        QCursor.setPos(center)

    def check_mouse_position(self):
        new_mouse_position = QCursor.pos()
        if new_mouse_position != self.mouse_position:
            self.show_image(self.photo_paths[self.current_image_index])
        self.mouse_position = new_mouse_position

    def load_images_paths(self,folder_path):     #folder_path 指定文件夹的路径
        photo_paths = [path for path in
                       glob(os.path.join(folder_path, "*.jpg")) + glob(os.path.join(folder_path, "*.png")) if os.path.isfile(path)]
        if not photo_paths:
            raise ValueError("No image files found in the folder.")
        return photo_paths

    def cal_function(self,b,pos):
        a = Gaussian(sigma, w)
        a.get_multi_resolution_pyramid(b)
        # pos = [self.mouse_position.x(), self.mouse_position.y()]
        a.get_vc_R_T(pos)
        a.get_blending_func()
        a.get_blending_image()
        return a.outputs[0]

    def show_image(self, image_path):
        # 读取图像
        img1 = cv2.imread(image_path)
        # 获取原始图像的尺寸
        img_height, img_width, _ = img1.shape
        # 将图像转换为Qt使用的格式
        h, w, c = img1.shape
        qImg = QImage(img1.data, w, h, w * c, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        scaled_width = scaled_pixmap.width()
        scaled_height = scaled_pixmap.height()
        # print("缩放后的宽度：", scaled_width)
        # print("缩放后的高度：", scaled_height)

        # 获取self.label的尺寸
        label_width = self.label.width()
        label_height = self.label.height()  # 计算鼠标在原始图像上的坐标
        # 获取鼠标在self.label上的坐标
        x,y = self.mouse_position.x(),self.mouse_position.y()
        # 获取缩放后的pixmap的左上角在self.label中的坐标
        pixmap_left = (label_width - scaled_width) / 2
        pixmap_top = (label_height - scaled_height) / 2
        # 计算鼠标在缩放后的pixmap上的坐标
        pixmap_x = int(x - pixmap_left)
        pixmap_y = int(y - pixmap_top)
        # 计算鼠标在原始图像上的坐标
        img_x = int(pixmap_x * img_width / scaled_width)
        img_y = int(pixmap_y * img_height / scaled_height)
        # img_x = int(x * img_width / scaled_width)
        # img_y = int(y * img_height / scaled_height)

        # 在原始图像上绘制一个圆形表示鼠标位置
        cv2.circle(img1, (img_x, img_y), 5, (0, 0, 255), -1)
        img2 = self.cal_function(img1,[img_x,img_y])
        # 将图像转换为Qt使用的格式
        h, w, c = img2.shape
        qImg = QImage(img2.data, w, h, w * c, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        # 在窗口中央显示图片
        # self.label.setPixmap(pixmap)
        self.label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def switch_image(self):
        # 切换到下一张图片，并重新设置计时器
        self.current_image_index = (self.current_image_index + 1) % len(self.photo_paths)
        self.show_image(self.photo_paths[self.current_image_index])
        self.timer.start(8000)
        self.setCursorPosition()  # 将鼠标放置于屏幕中心

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.timer.stop()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.mainwindow.show()
    app.exec_()

