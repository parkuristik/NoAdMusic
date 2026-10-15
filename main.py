import datetime
import json
import os
import shutil
import sys
import zlib
from PySide6.QtCore import QUrl, QUrlQuery, Qt, QSize, QRect, QRectF, QPointF, QPoint
from PySide6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QLinearGradient, QBrush,
    QFont, QIcon, QPen, QPolygonF
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QSlider, QListWidget, QListWidgetItem, QListView,
    QStackedWidget, QInputDialog, QMessageBox, QLineEdit, QMenu,
    QAbstractItemView, QStyle, QGraphicsDropShadowEffect, QButtonGroup
)

# Ключ для доступа к каталогу Jamendo
JAMENDO_CLIENT_ID = "ef3920b9"

# Служебное имя для «плейлиста» из результатов поиска
SEARCH_KEY = "__search__"

# Жанры для кнопок на странице поиска: (надпись, тег в Jamendo)
GENRES = [
    ("Поп", "pop"), ("Рок", "rock"), ("Электроника", "electronic"),
    ("Хип-хоп", "hiphop"), ("Джаз", "jazz"), ("Лоу-фай", "lofi"),
    ("Классика", "classical"), ("Эмбиент", "ambient"), ("Метал", "metal"),
    ("Фолк", "folk"), ("Инди", "indie"), ("Чилл", "chillout"), ("R&B", "rnb"),
]

# Папка программы (там лежат main.py и значок)
if getattr(sys, "frozen", False):
    APP_DIR = sys._MEIPASS  # когда программа собрана в .exe
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Данные (плейлисты и обложки) хранятся в папке пользователя:
# C:\Users\<имя>\AppData\Roaming\NoAdMusic
DATA_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "NoAdMusic")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_FILE = os.path.join(DATA_DIR, "playlists.json")   # плейлисты и треки
COVERS_FILE = os.path.join(DATA_DIR, "covers.json")    # обложки плейлистов
ICON_FILE = os.path.join(APP_DIR, "icon.ico")

# Один раз переносим старые файлы, которые лежали рядом с main.py
if not getattr(sys, "frozen", False):
    for file_name in ("playlists.json", "covers.json"):
        old_path = os.path.join(APP_DIR, file_name)
        new_path = os.path.join(DATA_DIR, file_name)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            shutil.copy(old_path, new_path)

# Оформление в стиле Spotify
STYLE = """
QWidget {
    background-color: #121212;
    color: #ffffff;
    font-family: "Segoe UI";
    font-size: 14px;
}
#root { background-color: #000000; }
#panel { background-color: #121212; border-radius: 10px; }
#bottom { background-color: #000000; }
#page, QStackedWidget { background: transparent; }
QLabel { background: transparent; }
QSlider { background: transparent; }

#logo { font-size: 20px; font-weight: bold; color: #1db954; }
#sectionTitle { color: #b3b3b3; font-weight: bold; font-size: 12px; }
#sectionHeader { font-size: 20px; font-weight: bold; }
#header { font-size: 30px; font-weight: bold; }
#pageTitle { font-size: 44px; font-weight: bold; }
#nowPlaying { font-weight: bold; }
#time { color: #b3b3b3; font-size: 12px; }

QListWidget { border: none; outline: none; background: transparent; }
QListWidget::item { padding: 10px 12px; border-radius: 6px; }
QListWidget::item:hover { background-color: #1f1f1f; }
QListWidget::item:selected { background-color: #2a2a2a; color: #1db954; }

#library::item { padding: 6px 8px; }
#results::item { padding: 6px 8px; }
#cards::item { padding: 10px; border-radius: 8px; color: #ffffff; }
#cards::item:hover { background-color: #1f1f1f; }
#cards::item:selected { background-color: #2a2a2a; color: #ffffff; }

QPushButton { border: none; }
QPushButton#accent {
    background-color: #1db954; color: #000000; font-weight: bold;
    border-radius: 18px; padding: 9px 20px;
}
QPushButton#accent:hover { background-color: #1ed760; }
QPushButton#ghost {
    background-color: transparent; color: #b3b3b3;
    border: 1px solid #535353; border-radius: 18px; padding: 8px 18px;
}
QPushButton#ghost:hover { color: #ffffff; border: 1px solid #ffffff; }
QPushButton#danger {
    background-color: transparent; color: #b3b3b3;
    border: 1px solid #535353; border-radius: 18px; padding: 8px 18px;
}
QPushButton#danger:hover { color: #ff6b6b; border: 1px solid #ff6b6b; }
QPushButton#chip {
    background-color: #2a2a2a; color: #ffffff;
    border-radius: 16px; padding: 7px 14px;
}
QPushButton#chip:hover { background-color: #3a3a3a; }
QPushButton#chip:checked { background-color: #ffffff; color: #000000; }
QPushButton#nav {
    background-color: transparent; color: #ffffff; font-weight: bold;
    font-size: 15px; text-align: left; padding: 10px 12px; border-radius: 6px;
}
QPushButton#nav:hover { background-color: #1f1f1f; }
QPushButton#icon { background-color: transparent; }
QPushButton#round { background-color: #ffffff; border-radius: 22px; }
QPushButton#round:hover { background-color: #f0f0f0; }

QSlider::groove:horizontal { height: 4px; background: #535353; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #1db954; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #ffffff; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px;
}

QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #4d4d4d; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QLineEdit {
    background-color: #2a2a2a; border: 1px solid #535353;
    border-radius: 6px; padding: 6px;
}
QLineEdit#searchBox {
    background-color: #242424; border: 1px solid #242424;
    border-radius: 19px; padding: 9px 18px; font-size: 15px;
}
QLineEdit#searchBox:focus { border: 1px solid #ffffff; }

QMenu {
    background-color: #282828; border: 1px solid #3a3a3a; padding: 4px;
}
QMenu::item { padding: 8px 24px; border-radius: 4px; }
QMenu::item:selected { background-color: #3a3a3a; }
QMenu::separator { height: 1px; background: #3a3a3a; margin: 4px 8px; }

QMessageBox QPushButton, QDialogButtonBox QPushButton {
    background-color: #2a2a2a; border-radius: 14px; padding: 6px 18px; min-width: 70px;
}
QMessageBox QPushButton:hover, QDialogButtonBox QPushButton:hover {
    background-color: #3a3a3a;
}
"""


# ---------- Вспомогательные функции ----------

def tracks_word(n):
    # "1 трек", "2 трека", "5 треков"
    last, last_two = n % 10, n % 100
    if last == 1 and last_two != 11:
        return "трек"
    if 2 <= last <= 4 and not 12 <= last_two <= 14:
        return "трека"
    return "треков"


def greeting():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


# Трек в плейлисте бывает двух видов:
#   - строка: путь к файлу на компьютере
#   - словарь: трек из интернета (название, исполнитель, ссылка, картинка)

def track_title(track):
    if isinstance(track, dict):
        return track.get("title", "")
    return os.path.splitext(os.path.basename(track))[0]


def track_artist(track):
    if isinstance(track, dict):
        return track.get("artist", "")
    return ""


def track_label(track):
    artist = track_artist(track)
    if artist:
        return f"{track_title(track)} — {artist}"
    return track_title(track)


def track_url(track):
    if isinstance(track, dict):
        return QUrl(track["url"])
    return QUrl.fromLocalFile(track)


def format_time(ms):
    seconds = max(ms, 0) // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def draw_symbol(kind, color):
    # Рисуем иконку сами, чтобы она подчинялась цветам, а не была эмодзи
    pix = QPixmap(96, 96)
    pix.setDevicePixelRatio(4.0)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))

    if kind == "play":
        painter.drawPolygon(QPolygonF([QPointF(7, 4), QPointF(20, 12), QPointF(7, 20)]))
    elif kind == "pause":
        painter.drawRect(QRectF(6, 4, 4, 16))
        painter.drawRect(QRectF(14, 4, 4, 16))
    elif kind == "prev":
        painter.drawRect(QRectF(5, 5, 2.5, 14))
        painter.drawPolygon(QPolygonF([QPointF(19, 5), QPointF(8.5, 12), QPointF(19, 19)]))
    elif kind == "next":
        painter.drawRect(QRectF(16.5, 5, 2.5, 14))
        painter.drawPolygon(QPolygonF([QPointF(5, 5), QPointF(15.5, 12), QPointF(5, 19)]))
    elif kind == "home":
        painter.drawPolygon(QPolygonF([
            QPointF(12, 3), QPointF(22, 12), QPointF(19, 12), QPointF(19, 20),
            QPointF(14, 20), QPointF(14, 14), QPointF(10, 14), QPointF(10, 20),
            QPointF(5, 20), QPointF(5, 12), QPointF(2, 12),
        ]))
    elif kind == "search":
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(color), 2.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(QRectF(4, 4, 11, 11))
        painter.drawLine(QPointF(13.5, 13.5), QPointF(20, 20))
    elif kind == "volume":
        painter.drawPolygon(QPolygonF([
            QPointF(3, 9), QPointF(7, 9), QPointF(12, 5),
            QPointF(12, 19), QPointF(7, 15), QPointF(3, 15),
        ]))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(color), 1.6))
        painter.drawArc(QRect(8, 8, 8, 8), -45 * 16, 90 * 16)
        painter.drawArc(QRect(5, 5, 14, 14), -45 * 16, 90 * 16)

    painter.end()
    return pix


def make_icon(kind, color="#b3b3b3", hover_color="#ffffff"):
    icon = QIcon()
    icon.addPixmap(draw_symbol(kind, color), QIcon.Normal)
    icon.addPixmap(draw_symbol(kind, hover_color), QIcon.Active)
    return icon


def make_cover(name, image, size, radius=8):
    # Обложка: картинка (путь к файлу или готовый QPixmap) или цветной градиент с буквой
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    clip = QPainterPath()
    clip.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(clip)

    if isinstance(image, QPixmap):
        source = image
    elif image and os.path.exists(image):
        source = QPixmap(image)
    else:
        source = QPixmap()

    if not source.isNull():
        scaled = source.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = (scaled.width() - size) // 2
        y = (scaled.height() - size) // 2
        painter.drawPixmap(0, 0, scaled, x, y, size, size)
    else:
        hue = zlib.crc32(name.encode("utf-8")) % 360
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0, QColor.fromHsv(hue, 170, 230))
        gradient.setColorAt(1, QColor.fromHsv((hue + 40) % 360, 200, 110))
        painter.fillRect(0, 0, size, size, QBrush(gradient))
        painter.setPen(QColor(255, 255, 255, 230))
        painter.setFont(QFont("Segoe UI", max(int(size * 0.3), 8), QFont.Bold))
        painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, name[:1].upper())

    painter.end()
    return pix


def cover_tint(name, image_path):
    # Главный цвет обложки: им подкрашивается верх страницы плейлиста
    if image_path and os.path.exists(image_path):
        pix = QPixmap(image_path)
        if not pix.isNull():
            n = 24
            img = pix.scaled(n, n, Qt.IgnoreAspectRatio, Qt.SmoothTransformation).toImage()
            r = g = b = 0
            for x in range(n):
                for y in range(n):
                    c = img.pixelColor(x, y)
                    r += c.red()
                    g += c.green()
                    b += c.blue()
            count = n * n
            hue, sat, val, _ = QColor(r // count, g // count, b // count).getHsv()
            if hue < 0:
                return QColor(100, 100, 100)
            return QColor.fromHsv(hue, max(min(sat, 230), 100), max(min(val, 180), 100))
    hue = zlib.crc32(name.encode("utf-8")) % 360
    return QColor.fromHsv(hue, 170, 170)


def enable_dark_title_bar(window):
    # Красим заголовок окна Windows в чёрный цвет
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(window.winId())
        dwm = ctypes.windll.dwmapi

        def set_attr(attr, value):
            v = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))

        set_attr(20, 1)           # тёмный режим заголовка
        set_attr(19, 1)           # то же для старых версий Windows 10
        set_attr(35, 0x00000000)  # чёрный цвет заголовка (Windows 11)
    except Exception:
        pass


# ---------- Свои элементы интерфейса ----------

class ClickSlider(QSlider):
    # Ползунок, который прыгает в то место, куда кликнули, и который можно тянуть
    def _jump(self, event):
        if self.maximum() <= self.minimum():
            return
        value = QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), int(event.position().x()), max(self.width(), 1)
        )
        self.setValue(value)
        self.sliderMoved.emit(value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSliderDown(True)
            self._jump(event)
            event.accept()

    def mouseMoveEvent(self, event):
        if self.isSliderDown():
            self._jump(event)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.isSliderDown():
            self._jump(event)
            self.setSliderDown(False)
            event.accept()


class GradientPage(QWidget):
    # Страница, у которой верх подкрашен цветным градиентом
    def __init__(self):
        super().__init__()
        self.setObjectName("page")
        self.tint = QColor(29, 185, 84)

    def set_tint(self, color):
        self.tint = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.setClipPath(path)
        top = QColor(self.tint)
        top.setAlpha(120)
        bottom = QColor(self.tint)
        bottom.setAlpha(0)
        gradient = QLinearGradient(0, 0, 0, 380)
        gradient.setColorAt(0, top)
        gradient.setColorAt(1, bottom)
        painter.fillRect(self.rect(), QBrush(gradient))


# ---------- Главное окно ----------

class Player(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowTitle("NoAdMusic")
        self.resize(1100, 700)
        self.setMinimumSize(900, 560)
        self.setStyleSheet(STYLE)

        self.playlists = self.load_playlists()   # название -> список треков
        self.covers = load_json(COVERS_FILE, {})  # название -> путь к картинке
        self.view_name = ""      # плейлист, который сейчас открыт на экране
        self.play_name = ""      # плейлист, из которого сейчас играет музыка
        self.current_index = -1  # номер играющего трека в play_name

        # Поиск и интернет
        self.network = QNetworkAccessManager(self)
        self.search_results = []     # то, что найдено последним поиском
        self.search_queue = []       # очередь, из которой играем результаты поиска
        self.search_generation = 0   # номер поиска (чтобы отбрасывать устаревшие ответы)
        self.search_loaded = False   # загружали ли уже «Популярное сейчас»
        self.image_cache = {}        # скачанные картинки: ссылка -> QPixmap

        # Движок воспроизведения
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)
        self.player.mediaStatusChanged.connect(self.on_status_changed)
        self.player.playbackStateChanged.connect(self.update_play_button)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.errorOccurred.connect(self.on_player_error)

        self.build_ui()
        self.refresh_playlist_views()
        if self.playlists:
            self.view_name = next(iter(self.playlists))
        self.show_home()

    # ---------- Построение интерфейса ----------

    def make_panel(self):
        panel = QWidget()
        panel.setObjectName("panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        return panel

    def build_ui(self):
        # Левая панель
        logo = QLabel("♫  NoAdMusic")
        logo.setObjectName("logo")

        home_button = QPushButton("  Главная")
        home_button.setObjectName("nav")
        home_button.setIcon(make_icon("home", "#ffffff"))
        home_button.setIconSize(QSize(22, 22))
        home_button.clicked.connect(self.show_home)

        search_nav_button = QPushButton("  Поиск")
        search_nav_button.setObjectName("nav")
        search_nav_button.setIcon(make_icon("search", "#ffffff"))
        search_nav_button.setIconSize(QSize(22, 22))
        search_nav_button.clicked.connect(self.show_search)

        section = QLabel("ТВОИ ПЛЕЙЛИСТЫ")
        section.setObjectName("sectionTitle")

        self.library = QListWidget()
        self.library.setObjectName("library")
        self.library.setIconSize(QSize(48, 48))
        self.library.itemClicked.connect(self.on_playlist_clicked)

        new_button = QPushButton("＋  Новый плейлист")
        new_button.setObjectName("accent")
        new_button.clicked.connect(self.new_playlist)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(16, 20, 16, 16)
        sidebar_layout.setSpacing(8)
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(home_button)
        sidebar_layout.addWidget(search_nav_button)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(section)
        sidebar_layout.addWidget(self.library, 1)
        sidebar_layout.addWidget(new_button)
        sidebar = self.make_panel()
        sidebar.setFixedWidth(270)
        sidebar.setLayout(sidebar_layout)

        # Страница 0: Главная (карточки плейлистов)
        home_title = QLabel(greeting())
        home_title.setObjectName("header")
        home_section = QLabel("ТВОИ ПЛЕЙЛИСТЫ")
        home_section.setObjectName("sectionTitle")
        self.home_hint = QLabel("Пока нет плейлистов. Нажми «＋ Новый плейлист» слева.")
        self.home_hint.setObjectName("time")

        self.cards = QListWidget()
        self.cards.setObjectName("cards")
        self.cards.setViewMode(QListView.IconMode)
        self.cards.setIconSize(QSize(170, 170))
        self.cards.setGridSize(QSize(194, 250))
        self.cards.setResizeMode(QListView.Adjust)
        self.cards.setMovement(QListView.Static)
        self.cards.setWordWrap(True)
        self.cards.setUniformItemSizes(True)
        self.cards.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards.itemClicked.connect(self.on_playlist_clicked)

        home_layout = QVBoxLayout()
        home_layout.setContentsMargins(24, 24, 24, 16)
        home_layout.setSpacing(10)
        home_layout.addWidget(home_title)
        home_layout.addSpacing(6)
        home_layout.addWidget(home_section)
        home_layout.addWidget(self.home_hint)
        home_layout.addWidget(self.cards, 1)
        self.home_page = GradientPage()
        self.home_page.setLayout(home_layout)

        # Страница 1: открытый плейлист
        self.page_cover = QLabel()
        self.page_cover.setFixedSize(200, 200)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 170))
        self.page_cover.setGraphicsEffect(shadow)

        kind_label = QLabel("ПЛЕЙЛИСТ")
        kind_label.setObjectName("sectionTitle")
        self.page_title = QLabel("")
        self.page_title.setObjectName("pageTitle")
        self.page_title.setWordWrap(True)
        self.page_meta = QLabel("")
        self.page_meta.setObjectName("time")

        play_view_button = QPushButton("Играть")
        play_view_button.setObjectName("accent")
        play_view_button.setIcon(make_icon("play", "#000000", "#000000"))
        play_view_button.setIconSize(QSize(16, 16))
        add_button = QPushButton("＋ Добавить с компьютера")
        add_button.setObjectName("ghost")
        cover_button = QPushButton("Обложка")
        cover_button.setObjectName("ghost")
        remove_button = QPushButton("Убрать выбранный трек")
        remove_button.setObjectName("ghost")
        delete_button = QPushButton("Удалить плейлист")
        delete_button.setObjectName("danger")
        play_view_button.clicked.connect(self.play_view)
        add_button.clicked.connect(self.add_tracks)
        cover_button.clicked.connect(self.change_cover)
        remove_button.clicked.connect(self.remove_track)
        delete_button.clicked.connect(self.delete_playlist)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(play_view_button)
        row1.addWidget(add_button)
        row1.addStretch(1)
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(cover_button)
        row2.addWidget(remove_button)
        row2.addWidget(delete_button)
        row2.addStretch(1)

        info = QVBoxLayout()
        info.setSpacing(6)
        info.addWidget(kind_label)
        info.addWidget(self.page_title)
        info.addWidget(self.page_meta)
        info.addStretch(1)
        info.addLayout(row1)
        info.addLayout(row2)

        top_row = QHBoxLayout()
        top_row.setSpacing(24)
        top_row.addWidget(self.page_cover)
        top_row.addLayout(info, 1)

        self.track_list = QListWidget()
        self.track_list.setObjectName("tracks")
        self.track_list.itemDoubleClicked.connect(self.on_item_double_clicked)

        playlist_layout = QVBoxLayout()
        playlist_layout.setContentsMargins(24, 24, 24, 16)
        playlist_layout.setSpacing(14)
        playlist_layout.addLayout(top_row)
        playlist_layout.addWidget(self.track_list, 1)
        self.playlist_page = GradientPage()
        self.playlist_page.setLayout(playlist_layout)

        # Страница 2: поиск
        search_title = QLabel("Поиск")
        search_title.setObjectName("header")
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBox")
        self.search_input.setPlaceholderText("Название, исполнитель или жанр")
        self.search_input.returnPressed.connect(self.start_search)
        search_button = QPushButton("Найти")
        search_button.setObjectName("accent")
        search_button.clicked.connect(self.start_search)
        self.add_to_playlist_button = QPushButton("＋ В плейлист")
        self.add_to_playlist_button.setObjectName("ghost")
        self.add_to_playlist_button.clicked.connect(self.add_selected_to_playlist)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(search_button)
        search_row.addWidget(self.add_to_playlist_button)

        # Кнопки жанров в два ряда
        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)
        chip_rows = []
        for genres in (GENRES[:6], GENRES[6:]):
            chip_row = QHBoxLayout()
            chip_row.setSpacing(8)
            for label, tag in genres:
                chip = QPushButton(label)
                chip.setObjectName("chip")
                chip.setCheckable(True)
                chip.clicked.connect(
                    lambda checked=False, l=label, t=tag: self.on_chip_clicked(l, t)
                )
                self.chip_group.addButton(chip)
                chip_row.addWidget(chip)
            chip_row.addStretch(1)
            chip_rows.append(chip_row)

        self.results_title = QLabel("")
        self.results_title.setObjectName("sectionHeader")
        self.search_status = QLabel("")
        self.search_status.setObjectName("time")

        self.results_list = QListWidget()
        self.results_list.setObjectName("results")
        self.results_list.setIconSize(QSize(56, 56))
        self.results_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)

        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(24, 24, 24, 16)
        search_layout.setSpacing(10)
        search_layout.addWidget(search_title)
        search_layout.addLayout(search_row)
        for chip_row in chip_rows:
            search_layout.addLayout(chip_row)
        search_layout.addSpacing(4)
        search_layout.addWidget(self.results_title)
        search_layout.addWidget(self.search_status)
        search_layout.addWidget(self.results_list, 1)
        self.search_page = GradientPage()
        self.search_page.setLayout(search_layout)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)      # 0
        self.stack.addWidget(self.playlist_page)  # 1
        self.stack.addWidget(self.search_page)    # 2

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)
        main_panel = self.make_panel()
        main_panel.setLayout(main_layout)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(8, 8, 8, 0)
        top_layout.setSpacing(8)
        top_layout.addWidget(sidebar)
        top_layout.addWidget(main_panel, 1)

        # Нижняя панель
        self.now_cover = QLabel()
        self.now_cover.setFixedSize(56, 56)
        self.now_playing = QLabel("Ничего не играет")
        self.now_playing.setObjectName("nowPlaying")
        self.now_playing.setMinimumWidth(10)
        self.now_playlist = QLabel("")
        self.now_playlist.setObjectName("time")
        self.now_playlist.setMinimumWidth(10)

        now_text = QVBoxLayout()
        now_text.setSpacing(2)
        now_text.addStretch(1)
        now_text.addWidget(self.now_playing)
        now_text.addWidget(self.now_playlist)
        now_text.addStretch(1)

        left_layout = QHBoxLayout()
        left_layout.setSpacing(12)
        left_layout.addWidget(self.now_cover)
        left_layout.addLayout(now_text, 1)

        prev_button = QPushButton()
        prev_button.setObjectName("icon")
        prev_button.setIcon(make_icon("prev"))
        prev_button.setIconSize(QSize(24, 24))
        prev_button.setFixedSize(36, 36)
        self.play_button = QPushButton()
        self.play_button.setObjectName("round")
        self.play_button.setIconSize(QSize(22, 22))
        self.play_button.setFixedSize(44, 44)
        next_button = QPushButton()
        next_button.setObjectName("icon")
        next_button.setIcon(make_icon("next"))
        next_button.setIconSize(QSize(24, 24))
        next_button.setFixedSize(36, 36)
        prev_button.clicked.connect(self.play_prev)
        self.play_button.clicked.connect(self.toggle_play)
        next_button.clicked.connect(self.play_next)
        self.update_play_button(QMediaPlayer.StoppedState)

        controls_row = QHBoxLayout()
        controls_row.addStretch(1)
        controls_row.addWidget(prev_button)
        controls_row.addWidget(self.play_button)
        controls_row.addWidget(next_button)
        controls_row.addStretch(1)

        self.time_current = QLabel("0:00")
        self.time_current.setObjectName("time")
        self.time_total = QLabel("0:00")
        self.time_total.setObjectName("time")
        self.progress_slider = ClickSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.sliderMoved.connect(self.player.setPosition)

        progress_row = QHBoxLayout()
        progress_row.addWidget(self.time_current)
        progress_row.addWidget(self.progress_slider, 1)
        progress_row.addWidget(self.time_total)

        center_layout = QVBoxLayout()
        center_layout.setSpacing(2)
        center_layout.addLayout(controls_row)
        center_layout.addLayout(progress_row)

        volume_icon = QLabel()
        volume_icon.setPixmap(make_icon("volume").pixmap(22, 22))
        self.volume_slider = ClickSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(110)
        self.volume_slider.valueChanged.connect(self.change_volume)

        volume_row = QHBoxLayout()
        volume_row.addStretch(1)
        volume_row.addWidget(volume_icon)
        volume_row.addWidget(self.volume_slider)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(20, 8, 20, 8)
        bottom_layout.addLayout(left_layout, 2)
        bottom_layout.addLayout(center_layout, 4)
        bottom_layout.addLayout(volume_row, 2)
        bottom = QWidget()
        bottom.setObjectName("bottom")
        bottom.setAttribute(Qt.WA_StyledBackground, True)
        bottom.setFixedHeight(96)
        bottom.setLayout(bottom_layout)

        # Собираем всё вместе
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(top_layout, 1)
        root.addWidget(bottom)
        self.setLayout(root)

    # ---------- Сохранение и загрузка ----------

    def load_playlists(self):
        data = load_json(SAVE_FILE, {})
        if not data:
            data = {"Мои треки": []}
        return data

    def save_playlists(self):
        save_json(SAVE_FILE, self.playlists)

    def save_covers(self):
        save_json(COVERS_FILE, self.covers)

    # ---------- Вспомогательные методы ----------

    def get_tracks(self, name):
        # Список треков плейлиста (или очередь из результатов поиска)
        if name == SEARCH_KEY:
            return self.search_queue
        return self.playlists.get(name, [])

    def display_name(self, name):
        return "Результаты поиска" if name == SEARCH_KEY else name

    def load_image(self, url, callback):
        # Скачивает картинку в фоне и вызывает callback(картинка), когда готово
        if url in self.image_cache:
            callback(self.image_cache[url])
            return
        reply = self.network.get(QNetworkRequest(QUrl(url)))

        def done():
            if reply.error() == QNetworkReply.NoError:
                pix = QPixmap()
                if pix.loadFromData(reply.readAll()):
                    self.image_cache[url] = pix
                    callback(pix)
            reply.deleteLater()

        reply.finished.connect(done)

    # ---------- Показ плейлистов ----------

    def refresh_playlist_views(self):
        # Перерисовываем карточки на главной и список в левой панели
        self.cards.clear()
        self.library.clear()
        for name, tracks in self.playlists.items():
            subtitle = f"{len(tracks)} {tracks_word(len(tracks))}"
            cover = self.covers.get(name)

            card = QListWidgetItem(QIcon(make_cover(name, cover, 170, 10)), f"{name}\n{subtitle}")
            card.setData(Qt.UserRole, name)
            self.cards.addItem(card)

            row = QListWidgetItem(QIcon(make_cover(name, cover, 48, 4)), f"{name}\n{subtitle}")
            row.setData(Qt.UserRole, name)
            self.library.addItem(row)

        self.home_hint.setVisible(not self.playlists)

        if self.stack.currentIndex() == 1:
            for i in range(self.library.count()):
                if self.library.item(i).data(Qt.UserRole) == self.view_name:
                    self.library.setCurrentRow(i)

    def refresh_track_view(self):
        name = self.view_name
        tracks = self.playlists.get(name, [])
        cover = self.covers.get(name)
        self.page_title.setText(name)
        self.page_meta.setText(f"{len(tracks)} {tracks_word(len(tracks))}")
        self.page_cover.setPixmap(make_cover(name, cover, 200, 10))
        self.playlist_page.set_tint(cover_tint(name, cover))
        self.track_list.clear()
        for i, track in enumerate(tracks, 1):
            self.track_list.addItem(f"{i:>2}     {track_label(track)}")
        self.highlight_current()

    def highlight_current(self):
        if self.view_name == self.play_name and self.current_index >= 0:
            self.track_list.setCurrentRow(self.current_index)

    def show_home(self):
        self.stack.setCurrentIndex(0)
        self.cards.clearSelection()
        self.library.clearSelection()

    def show_search(self):
        self.stack.setCurrentIndex(2)
        self.cards.clearSelection()
        self.library.clearSelection()
        self.search_input.setFocus()
        if not self.search_loaded:
            self.search_loaded = True
            self.load_popular()

    def open_playlist(self, name):
        self.view_name = name
        self.refresh_track_view()
        self.stack.setCurrentIndex(1)

    def on_playlist_clicked(self, item):
        self.open_playlist(item.data(Qt.UserRole))

    # ---------- Работа с плейлистами ----------

    def ask_playlist_name(self):
        # Спрашивает название; возвращает "" если отменили или такое уже есть
        name, ok = QInputDialog.getText(self, "Новый плейлист", "Название:")
        name = name.strip()
        if not ok or not name or name in self.playlists:
            return ""
        return name

    def new_playlist(self):
        name = self.ask_playlist_name()
        if not name:
            return
        self.playlists[name] = []
        self.save_playlists()
        self.refresh_playlist_views()
        self.open_playlist(name)
        self.refresh_playlist_views()

    def delete_playlist(self):
        name = self.view_name
        if name not in self.playlists:
            return
        answer = QMessageBox.question(
            self, "Удалить плейлист",
            f"Удалить плейлист «{name}»?\nФайлы с музыкой на компьютере останутся."
        )
        if answer != QMessageBox.Yes:
            return
        if name == self.play_name:
            self.stop_playback()
        del self.playlists[name]
        self.covers.pop(name, None)
        self.save_playlists()
        self.save_covers()
        self.view_name = ""
        self.refresh_playlist_views()
        self.show_home()

    def change_cover(self):
        if self.view_name not in self.playlists:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите картинку для обложки", "",
            "Картинки (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:
            return
        self.covers[self.view_name] = path
        self.save_covers()
        self.refresh_playlist_views()
        self.refresh_track_view()
        if self.view_name == self.play_name:
            self.update_now_cover()

    # ---------- Работа с треками плейлиста ----------

    def add_tracks(self):
        if self.view_name not in self.playlists:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Выберите треки", "", "Аудио (*.mp3 *.wav *.flac *.ogg *.m4a)"
        )
        if not paths:
            return
        tracks = self.playlists[self.view_name]
        first_new = len(tracks)
        tracks.extend(paths)
        self.save_playlists()
        self.refresh_track_view()
        self.refresh_playlist_views()
        if self.current_index == -1:
            self.play_track(first_new, self.view_name)

    def remove_track(self):
        tracks = self.playlists.get(self.view_name)
        row = self.track_list.currentRow()
        if tracks is None or row < 0:
            return
        del tracks[row]
        if self.view_name == self.play_name:
            if row == self.current_index:
                self.stop_playback()
            elif row < self.current_index:
                self.current_index -= 1
        self.save_playlists()
        self.refresh_track_view()
        self.refresh_playlist_views()

    # ---------- Поиск в Jamendo ----------

    def clear_chips(self):
        self.chip_group.setExclusive(False)
        for button in self.chip_group.buttons():
            button.setChecked(False)
        self.chip_group.setExclusive(True)

    def load_popular(self):
        self.clear_chips()
        self.run_query("Популярное сейчас", {"order": "popularity_week", "limit": 40})

    def on_chip_clicked(self, label, tag):
        self.search_input.clear()
        self.run_query(label, {
            "tags": tag, "featured": 1, "groupby": "artist_id",
            "boost": "popularity_month", "limit": 40,
        })

    def start_search(self):
        text = self.search_input.text().strip()
        if not text:
            self.load_popular()
            return
        self.clear_chips()
        self.run_query(f"Результаты: «{text}»", {
            "search": text, "boost": "popularity_month", "limit": 40,
        })

    def run_query(self, title, params):
        self.search_generation += 1
        generation = self.search_generation
        self.results_title.setText(title)
        self.search_status.setText("Загружаю...")

        url = QUrl("https://api.jamendo.com/v3.0/tracks/")
        query = QUrlQuery()
        query.addQueryItem("client_id", JAMENDO_CLIENT_ID)
        query.addQueryItem("format", "json")
        for key, value in params.items():
            query.addQueryItem(key, str(value))
        url.setQuery(query)

        reply = self.network.get(QNetworkRequest(url))
        reply.finished.connect(lambda: self.on_search_finished(reply, generation))

    def on_search_finished(self, reply, generation):
        reply.deleteLater()
        if generation != self.search_generation:
            return  # уже запущен более новый запрос
        if reply.error() != QNetworkReply.NoError:
            self.search_status.setText("Не удалось подключиться к Jamendo. Проверь интернет.")
            return
        try:
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except Exception:
            self.search_status.setText("Jamendo вернул непонятный ответ")
            return

        headers = data.get("headers", {})
        if headers.get("status") != "success":
            self.search_status.setText("Ошибка Jamendo: " + str(headers.get("error_message", "неизвестная")))
            return

        results = []
        for item in data.get("results", []):
            audio = item.get("audio")
            if not audio:
                continue
            try:
                duration = int(item.get("duration") or 0)
            except (TypeError, ValueError):
                duration = 0
            results.append({
                "id": item.get("id"),
                "title": item.get("name") or "Без названия",
                "artist": item.get("artist_name") or "",
                "url": audio,
                "image": item.get("image") or "",
                "duration": duration,
            })

        self.search_results = results
        self.results_list.clear()
        for i, track in enumerate(results):
            placeholder = QIcon(make_cover(track["title"], None, 56, 4))
            meta = track["artist"]
            if track["duration"]:
                meta += f"  ·  {format_time(track['duration'] * 1000)}"
            item = QListWidgetItem(placeholder, f"{track['title']}\n{meta}")
            item.setData(Qt.UserRole, i)
            self.results_list.addItem(item)
            if track["image"]:
                self.load_image(
                    track["image"],
                    lambda pix, i=i: self.set_result_icon(generation, i, pix)
                )

        if results:
            self.search_status.setText(
                f"{len(results)} {tracks_word(len(results))}. "
                "Двойной клик: слушать. Ctrl+клик: выбрать несколько."
            )
        else:
            self.search_status.setText("Ничего не найдено")

    def set_result_icon(self, generation, index, pix):
        if generation != self.search_generation or index >= self.results_list.count():
            return
        self.results_list.item(index).setIcon(QIcon(make_cover("", pix, 56, 4)))

    def on_result_double_clicked(self, item):
        self.play_from_search(item.data(Qt.UserRole))

    def play_from_search(self, index):
        # Запоминаем найденное как очередь, чтобы новый поиск её не ломал
        self.search_queue = list(self.search_results)
        self.play_track(index, SEARCH_KEY)

    def add_selected_to_playlist(self):
        indexes = sorted(item.data(Qt.UserRole) for item in self.results_list.selectedItems())
        if not indexes:
            self.search_status.setText("Сначала выбери трек в списке (можно несколько, с зажатым Ctrl)")
            return

        # Меню со списком плейлистов
        menu = QMenu(self)
        for name in self.playlists:
            action = menu.addAction(name)
            action.setData(name)
        menu.addSeparator()
        new_action = menu.addAction("＋ Новый плейлист...")
        button = self.add_to_playlist_button
        chosen = menu.exec(button.mapToGlobal(QPoint(0, button.height())))
        if chosen is None:
            return

        if chosen is new_action:
            name = self.ask_playlist_name()
            if not name:
                return
            self.playlists[name] = []
        else:
            name = chosen.data()

        tracks = self.playlists[name]
        existing = {t["url"] for t in tracks if isinstance(t, dict)}
        added = 0
        for i in indexes:
            track = self.search_results[i]
            if track["url"] in existing:
                continue
            tracks.append(dict(track))
            existing.add(track["url"])
            added += 1

        self.save_playlists()
        self.refresh_playlist_views()
        self.search_status.setText(f"Добавлено в «{name}»: {added}")

    # ---------- Воспроизведение ----------

    def play_track(self, index, name):
        tracks = self.get_tracks(name)
        if not 0 <= index < len(tracks):
            return
        track = tracks[index]
        self.play_name = name
        self.current_index = index
        self.player.setSource(track_url(track))
        self.player.play()
        self.now_playing.setText(track_title(track))
        artist = track_artist(track)
        place = self.display_name(name)
        self.now_playlist.setText(f"{artist} · {place}" if artist else place)
        self.update_now_cover()
        self.highlight_current()

    def update_now_cover(self):
        tracks = self.get_tracks(self.play_name)
        track = tracks[self.current_index] if 0 <= self.current_index < len(tracks) else None
        self.now_cover.setPixmap(
            make_cover(self.display_name(self.play_name), self.covers.get(self.play_name), 56, 4)
        )
        # У интернет-треков показываем обложку альбома
        if isinstance(track, dict) and track.get("image"):
            index, play_name = self.current_index, self.play_name
            self.load_image(track["image"], lambda pix: self.set_now_cover(pix, index, play_name))

    def set_now_cover(self, pix, index, play_name):
        if self.current_index == index and self.play_name == play_name:
            self.now_cover.setPixmap(make_cover("", pix, 56, 4))

    def stop_playback(self):
        self.player.stop()
        self.current_index = -1
        self.play_name = ""
        self.now_playing.setText("Ничего не играет")
        self.now_playlist.setText("")
        self.now_cover.clear()

    def play_view(self):
        # Кнопка «Играть» на странице плейлиста
        if self.get_tracks(self.view_name):
            self.play_track(0, self.view_name)

    def play_next(self):
        tracks = self.get_tracks(self.play_name)
        if not tracks:
            return
        self.play_track((self.current_index + 1) % len(tracks), self.play_name)

    def play_prev(self):
        tracks = self.get_tracks(self.play_name)
        if not tracks:
            return
        self.play_track((self.current_index - 1) % len(tracks), self.play_name)

    def toggle_play(self):
        if self.current_index == -1:
            if self.stack.currentIndex() == 2 and self.search_results:
                self.play_from_search(0)
            else:
                self.play_view()
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    # ---------- Реакции на события плеера ----------

    def on_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()

    def on_player_error(self, error, message):
        if error != QMediaPlayer.NoError:
            self.now_playlist.setText("Не удалось воспроизвести этот трек")

    def update_play_button(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(make_icon("pause", "#000000", "#000000"))
        else:
            self.play_button.setIcon(make_icon("play", "#000000", "#000000"))

    def on_position_changed(self, position):
        # Не двигаем ползунок, пока пользователь сам его тянет
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)
        self.time_current.setText(format_time(position))

    def on_duration_changed(self, duration):
        self.progress_slider.setRange(0, duration)
        self.time_total.setText(format_time(duration))

    def on_item_double_clicked(self, item):
        self.play_track(self.track_list.row(item), self.view_name)

    def change_volume(self, value):
        self.audio_output.setVolume(value / 100)


# Чтобы значок правильно показывался на панели задач Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("noadmusic.player")
    except Exception:
        pass

app = QApplication(sys.argv)
app.setWindowIcon(QIcon(ICON_FILE))
try:
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
except Exception:
    pass
window = Player()
window.show()
enable_dark_title_bar(window)
sys.exit(app.exec())