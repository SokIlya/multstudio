from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QAction, QDialog, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QMainWindow, QMenu,
                             QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
                             QVBoxLayout, QWidget, QInputDialog, QMessageBox)

import cv2
import dao
import base64
import numpy as np
import os
import glob


class StartDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MultStudio')
        self.layout = QVBoxLayout(self)
        self.setFixedSize(250, 300)

        image_label = QLabel(self)
        pixmap = QPixmap('resources/logo.png')
        image_label.setPixmap(pixmap)
        image_label.setScaledContents(True)
        image_label.setFixedSize(200, 100)

        self.layout.addStretch()
        self.layout.addWidget(image_label, 0, Qt.AlignCenter)
        self.layout.addStretch()

        self.selected = False

        self.new_project_button = QPushButton('Новый проект')
        self.new_project_button.clicked.connect(self.parent().new_project)
        self.layout.addWidget(self.new_project_button)

        self.edit_project_button = QPushButton('Редактировать проект')
        self.edit_project_button.clicked.connect(self.parent().edit_project)
        self.layout.addWidget(self.edit_project_button)

        self.layout.addStretch()

        self.ok_button = QPushButton('OK')
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.close_dialog)
        self.ok_button.setStyleSheet("background-color:#1b1b1c;")
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def enable_ok_button(self):
        self.selected = True
        self.ok_button.setEnabled(True)
        self.ok_button.setStyleSheet("background-color:grey;")

    def close_dialog(self):
        if self.selected:
            self.accept()


class FrameAnimationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('MultStudio')
        self.start_dialog = None
        self.current_directory = "test_project"
        self.data_base = dao.DAO("db.db")
        self.project_title = QLabel()
        self.frame_list_widget = QListWidget()
        self.create_project()

        self.label_fps = QLabel('Кадров в секунду (FPS):')
        self.spinbox_fps = QSpinBox()
        self.spinbox_fps.setFixedWidth(100)
        self.spinbox_fps.setRange(1, 60)
        self.spinbox_fps.setValue(2)

        self.init_camera()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_video)

        self.frame = QLabel()
        self.create_button = QPushButton('Создать кадр')
        self.create_button.clicked.connect(self.create_frame)

        buttons_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttons_layout.addItem(spacer)
        self.delete_all_frames_button = QPushButton('Удалить все кадры')
        self.delete_all_frames_button.clicked.connect(self.delete_all_frames)
        self.delete_all_frames_button.setFixedSize(150, 30)
        buttons_layout.addWidget(self.delete_all_frames_button)

        self.frame_list = QLabel()
        self.create_mp4_button = QPushButton('Готово')
        self.create_mp4_button.clicked.connect(self.create_mp4)

        layout = QVBoxLayout()
        layout.addWidget(self.frame)
        layout.addWidget(self.project_title)
        layout.addWidget(self.create_button)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.label_fps)
        layout.addWidget(self.spinbox_fps)
        layout.addWidget(self.frame_list)
        layout.addWidget(self.create_mp4_button)

        layout.addWidget(self.frame_list_widget)
        self.update_frame_list()

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)
        self.timer.start(30)

        self.menuBar = self.menuBar()

        self.fileMenu = QMenu("&Файл", self)
        self.menuBar.addMenu(self.fileMenu)

        self.newProjectAction = QAction("&Новый проект", self)
        self.newProjectAction.triggered.connect(self.new_project)
        self.fileMenu.addAction(self.newProjectAction)

        self.editProjectAction = QAction("&Открыть проект", self)
        self.editProjectAction.triggered.connect(self.edit_project)
        self.fileMenu.addAction(self.editProjectAction)

    def show_start_dialog(self):
        self.start_dialog = StartDialog(self)
        status = self.start_dialog.exec_()
        return status

    def create_project(self):
        dir_name = f'projects/{self.current_directory}'
        if not os.path.isdir(dir_name):
            self.create_new_folder(f'projects/{self.current_directory}')
            self.update_frame_list()

    def delete_frame(self, frame_id):
        self.data_base.delete_frame(self.current_directory, frame_id)
        self.update_frame_list()

    def delete_all_frames(self):
        self.data_base.delete_all_frames(self.current_directory)
        self.update_frame_list()

    def update_frame_list(self):
        self.project_title.setText(f"Текущий проект: {self.current_directory}")
        self.frame_list_widget.clear()

        last_frame_id = self.data_base.get_last_frame_id(self.current_directory)

        for i in range(1, last_frame_id + 1):
            frame_data_base64 = self.data_base.get_frame(self.current_directory, i)
            if frame_data_base64 is not None:
                frame_data = base64.b64decode(frame_data_base64)
                frame_image = QImage.fromData(frame_data, "JPG")
                if frame_image.isNull():
                    # print(f"Failed to load frame {i}")  # debug
                    continue

                frame_widget = QWidget()
                frame_layout = QHBoxLayout(frame_widget)

                frame_label = QLabel()
                frame_pixmap = QPixmap.fromImage(frame_image)
                frame_label.setPixmap(frame_pixmap.scaled(100, 75, Qt.KeepAspectRatio))
                frame_layout.addWidget(frame_label)

                delete_button = QPushButton("Удалить")
                delete_button.clicked.connect(lambda checked, frame_id=i: self.delete_frame(frame_id))
                frame_layout.addWidget(delete_button)

                list_item = QListWidgetItem(self.frame_list_widget)
                list_item.setSizeHint(frame_widget.sizeHint())
                self.frame_list_widget.addItem(list_item)
                self.frame_list_widget.setItemWidget(list_item, frame_widget)
                # print(f"Frame {i} added to list")  # debug
            # else:
            # print(f"No data for frame {i}")  # debug

    def find_camera_index(self):
        max_tested = 10
        for index in range(max_tested):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.isOpened():
                cap.release()
                return index
        return -1

    def init_camera(self):
        camera_index = self.find_camera_index()
        if camera_index != -1:
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        else:
            QMessageBox.critical(self, "Ошибка", "Камера не подключена")
            self.close()

    def create_new_folder(self, folder_name):
        os.makedirs(folder_name)

    def new_project(self):
        project_name, ok = QInputDialog.getText(self, "Новый проект", "Введите название проекта:")
        if ok and project_name:
            self.current_directory = project_name
            self.create_project()
            self.start_dialog.enable_ok_button()

    def edit_project(self):
        directories = [d.name for d in os.scandir("projects") if d.is_dir()]
        directory_name, ok = QInputDialog.getItem(self, "Редактировать проект", "Выберите проект:", directories, 0,
                                                  False)
        if ok and directory_name:
            self.current_directory = directory_name
            self.start_dialog.enable_ok_button()
            self.update_frame_list()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            self.frame.setPixmap(QPixmap.fromImage(p))

    def create_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Конвертируем в RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Кодируем в base64
            _, buffer = cv2.imencode('.jpg', rgb_frame)
            frame_data = base64.b64encode(buffer)
            # Сохраняем в базу
            self.data_base.save_frame(self.current_directory, frame_data)
            # Обновляем кадры в интерфейсе
            self.update_frame_list()

    def create_mp4(self):
        try:
            fps = self.spinbox_fps.value()
            project_folder = os.path.abspath(f'projects/{self.current_directory}')
            existing_mp4_files = glob.glob(os.path.join(project_folder, '*.mp4'))
            next_file_id = len(existing_mp4_files) + 1
            output_filename = f'{self.current_directory}_{next_file_id}.mp4'
            output_filepath = os.path.join(project_folder, output_filename)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_filepath, fourcc, fps, (640, 480))

            last_frame_id = self.data_base.get_last_frame_id(self.current_directory)

            # Получаем кадры из базы данных и преобразуем их в MP4
            for i in range(1, last_frame_id + 1):
                frame_data_base64 = self.data_base.get_frame(self.current_directory, i)
                if frame_data_base64 is not None:
                    frame_data = base64.b64decode(frame_data_base64)
                    frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    if bgr_frame is not None:
                        out.write(bgr_frame)
                    else:
                        print(f"Failed to decode frame {i}")
                else:
                    print(f"No data for frame {i}")

            out.release()
            self.frame_list.setText(f"MP4 создан с именем {output_filename}")

            # Открываем папку с файлом
            os.startfile(project_folder)

        except Exception as e:
            print(f"An error occurred: {e}")


def load_stylesheet(file_path):
    with open(file_path, "r") as file:
        return file.read()


app = QApplication([])
stylesheet = load_stylesheet("resources/styles.qss")
app.setStyleSheet(stylesheet)
window = FrameAnimationApp()
ok = window.show_start_dialog()
if ok:
    window.show()
    app.exec_()
