import sys
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QGuiApplication, QImage, QPainter, QColor, QLinearGradient, QBrush, QPolygonF
)

app = QGuiApplication(sys.argv)
size = 256
image = QImage(size, size, QImage.Format_ARGB32)
image.fill(Qt.transparent)

p = QPainter(image)
p.setRenderHint(QPainter.Antialiasing)
p.setPen(Qt.NoPen)

# Тёмный скруглённый квадрат
p.setBrush(QColor("#121212"))
p.drawRoundedRect(QRectF(0, 0, size, size), 56, 56)

# Зелёный круг с градиентом
gradient = QLinearGradient(0, 0, size, size)
gradient.setColorAt(0, QColor("#1ed760"))
gradient.setColorAt(1, QColor("#128a3e"))
p.setBrush(QBrush(gradient))
p.drawEllipse(QRectF(24, 24, 208, 208))

# Две ноты со связкой
p.setBrush(QColor("#0b0b0b"))
for cx, cy in ((92, 180), (160, 160)):
    p.save()
    p.translate(cx, cy)
    p.rotate(-20)
    p.drawEllipse(QRectF(-24, -18, 48, 36))
    p.restore()
p.drawRect(QRectF(110, 78, 8, 98))
p.drawRect(QRectF(178, 58, 8, 98))
p.drawPolygon(QPolygonF([
    QPointF(110, 78), QPointF(186, 58), QPointF(186, 88), QPointF(110, 108)
]))
p.end()

image.save("icon.png")
image.save("icon.ico")
print("Готово: icon.png и icon.ico созданы")