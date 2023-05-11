#2023/5/11 14:53
总的说明   App文件夹中的的image_file为显著点的照片集
          App文件夹中的IMAGE为app的程序图标照片（ui）
          App文件夹中的ui为用ui写的MainWindow的设计页面
          py文件的话可以忽略clone、main和初始可以，目前只用实现功能py
实现功能.py的说明：
目前已经实现的功能，有初始的开始界面，在开始界面可以进入全屏的图片显示，在图片显示界面自动每隔一段时间切换下一张图片，并且鼠标会自动回到屏幕的中间，下面会解释如何根据鼠标的移动来更新照片（应该需要优化，不然速度很慢，且内部有重复的部分）
首先，有三个类，分别是class Gaussian，class MainWindow，class FullscreenImageWindow(QMainWindow)：
(注意此程序使用的是Pyside2）
class Gaussian是负责计算图片的类 略
class MainWindow则是开始界面，界面的布局使用的是ui设计的，因此是直接加载；在点击按钮后关闭自身显示另一个窗口（即FullscreenImageWindow）
class FullscreenImageWindow(QMainWindow)  ：
  这个类内部有def setCursorPosition(self)，def check_mouse_position(self)，
  def load_images_paths(self,folder_path)，def cal_function(self,b,pos)，
  def show_image(self, image_path)，def switch_image(self)，def keyPressEvent(self, event)，
  def closeEvent(self, event)这几个实例方法
  
  def setCursorPosition(self)是用来将鼠标置于屏幕中央的
  def check_mouse_position(self)是用来检察鼠标位置是否改变，若改变的话就通过计算更新图片（同时更新鼠标坐标来作为参数计算图片）（用了 def show_image(self, image_path)）
  def load_images_paths(self,folder_path)加载显著点图片的文件夹中的图片
  def cal_function(self,b,pos)计算新的照片，参数pos为鼠标的坐标
  def show_image(self, image_path)显示图片，具体先将img1通过cv2读取，随后将其转换为qt使用的格式，并通过他的缩放比例计算出鼠标实际在原图中的坐标（由于QT显示图片的时候进行了缩放，从而导致屏幕中鼠标的坐标并不等于鼠标在照片中的坐标），然后通过def cal_function(self,b,pos)计算出了新的照片（cal使用的是CV2计算的）将其转换为QT使用的格式将其在屏幕中显示出来
  def switch_image(self)设置定时器，到了以后切换下一张的照片并引用  def setCursorPosition(self)将鼠标置于屏幕中间。
  
