"""Configure heading and north arrow for the viewer and new web exports."""
import base64
import os

from qgis.PyQt.QtCore import QByteArray, QSettings, Qt
from qgis.PyQt.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDialog,
    QDialogButtonBox, QFileDialog, QFontComboBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout)
from qgis.PyQt.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from qgis.PyQt.QtSvg import QSvgRenderer

KEY = '/Qgis2threejsDecimalDegrees/presentation/'


def browser_svg(contents):
    """Supply concrete defaults for the QGIS-specific SVG colour parameters."""
    return (contents.replace(b'param(fill)', b'#111111').replace(b'param(outline)', b'#111111')
            .replace(b'param(fill-opacity)', b'1').replace(b'param(outline-opacity)', b'1')
            .replace(b'param(outline-width)', b'1'))


def preview_icon(path):
    with open(path, 'rb') as file:
        renderer = QSvgRenderer(QByteArray(browser_svg(file.read())))
    if not renderer.isValid(): return QIcon()
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try: renderer.render(painter)
    finally: painter.end()
    return QIcon(pixmap)


def read_options():
    settings = QSettings()
    def value(name, default, kind=str):
        return settings.value(KEY + name, default, type=kind)
    arrow_path = value('custom_file', '') if value('arrow_design', 'none') == 'custom' else ''
    design = value('arrow_design', 'none')
    if design.startswith('NorthArrow_') and design.endswith('.svg') and os.path.basename(design) == design:
        arrow_path = os.path.join(os.path.dirname(__file__), 'north_arrows', design)
    arrow_src = ''
    if arrow_path:
        with open(arrow_path, 'rb') as file:
            contents = file.read(2 * 1024 * 1024 + 1)
        if len(contents) > 2 * 1024 * 1024:
            raise ValueError('North-arrow image must be at most 2 MB')
        extension = os.path.splitext(arrow_path)[1].lower()
        if extension == '.svg':
            # QGIS parameter tokens are not understood by a browser.
            contents = browser_svg(contents)
            mime = 'image/svg+xml'
        elif extension == '.png':
            mime = 'image/png'
        else:
            raise ValueError('Choose an SVG or PNG north arrow')
        arrow_src = 'data:' + mime + ';base64,' + base64.b64encode(contents).decode('ascii')
    return {
        'heading': {'text': value('heading', ''), 'font': value('font', 'Sans Serif'),
                    'size': value('font_size', 24, int), 'bold': value('bold', False, bool),
                    'italic': value('italic', False, bool), 'color': value('color', '#000000')},
        'arrow': {'src': arrow_src, 'size': value('arrow_size', 64, int),
                  'position': value('position', 'right')},
    }


class PresentationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Viewer heading and north arrow')
        settings = QSettings()
        self.heading = QLineEdit(settings.value(KEY + 'heading', '', type=str))
        self.font = QFontComboBox()
        self.font.setCurrentFont(QFont(settings.value(KEY + 'font', 'Sans Serif', type=str)))
        self.size = QSpinBox(); self.size.setRange(8, 96)
        self.size.setValue(settings.value(KEY + 'font_size', 24, type=int))
        self.bold = QCheckBox('Bold'); self.bold.setChecked(settings.value(KEY + 'bold', False, type=bool))
        self.italic = QCheckBox('Italic'); self.italic.setChecked(settings.value(KEY + 'italic', False, type=bool))
        self.color = settings.value(KEY + 'color', '#000000', type=str)
        self.color_button = QPushButton('Choose colour')
        self.color_button.clicked.connect(self.choose_color)
        self.design = QComboBox(); self.design.addItem('None', 'none')
        for number in range(1, 12):
            filename = 'NorthArrow_{:02d}.svg'.format(number)
            path = os.path.join(os.path.dirname(__file__), 'north_arrows', filename)
            self.design.addItem(preview_icon(path), 'North arrow {:02d}'.format(number), filename)
        self.design.addItem('Custom SVG or PNG', 'custom')
        index = self.design.findData(settings.value(KEY + 'arrow_design', 'none', type=str))
        self.design.setCurrentIndex(max(0, index))
        self.custom = QLineEdit(settings.value(KEY + 'custom_file', '', type=str))
        browse = QPushButton('Browse…'); browse.clicked.connect(self.choose_file)
        self.arrow_size = QSpinBox(); self.arrow_size.setRange(20, 300)
        self.arrow_size.setValue(settings.value(KEY + 'arrow_size', 64, type=int))
        self.position = QComboBox(); self.position.addItem('Top right', 'right'); self.position.addItem('Top left', 'left')
        self.position.setCurrentIndex(max(0, self.position.findData(settings.value(KEY + 'position', 'right', type=str))))
        form = QFormLayout()
        form.addRow('Heading', self.heading); form.addRow('Font', self.font); form.addRow('Font size (px)', self.size)
        style = QHBoxLayout(); style.addWidget(self.bold); style.addWidget(self.italic); style.addWidget(self.color_button)
        form.addRow('Style', style); form.addRow('North arrow', self.design)
        custom_row = QHBoxLayout(); custom_row.addWidget(self.custom); custom_row.addWidget(browse)
        form.addRow('Custom arrow', custom_row); form.addRow('Arrow size (px)', self.arrow_size); form.addRow('Position', self.position)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self); layout.addLayout(form)
        layout.addWidget(QLabel('Heading and arrow are included in newly exported web scenes.'))
        layout.addWidget(buttons)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid(): self.color = color.name()

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Choose north arrow', '', 'Images (*.svg *.png)')
        if path:
            self.custom.setText(path)
            self.design.setCurrentIndex(self.design.findData('custom'))

    def save(self):
        values = {'heading': self.heading.text(), 'font': self.font.currentFont().family(),
                  'font_size': self.size.value(), 'bold': self.bold.isChecked(), 'italic': self.italic.isChecked(),
                  'color': self.color, 'arrow_design': self.design.currentData(), 'custom_file': self.custom.text(),
                  'arrow_size': self.arrow_size.value(), 'position': self.position.currentData()}
        settings = QSettings()
        for name, value in values.items(): settings.setValue(KEY + name, value)
