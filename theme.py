from PySide6 import QtGui


def apply_dark_theme(app) -> None:
    """Apply dark color palette to the application."""
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("white"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(35, 35, 35))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("white"))
    app.setPalette(palette)


def apply_light_theme(app) -> None:
    """Reset to default light theme."""
    app.setPalette(QtGui.QPalette())
