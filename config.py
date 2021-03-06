#!/usr/bin/env python3

import math
import os
import json
from functools import partial

from PyQt5.Qt import (  # pylint: disable=no-name-in-module
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    Qt,
)

from PyQt5.QtGui import QPixmap   # pylint: disable=no-name-in-module
from calibre.constants import numeric_version  # pylint: disable=no-name-in-module, disable=import-error
from calibre.devices.usbms.driver import debug_print as root_debug_print  # pylint: disable=no-name-in-module, disable=import-error
from calibre.utils.config import JSONConfig  # pylint: disable=no-name-in-module, disable=import-error
from calibre_plugins.koreader import clean_bookmarks  # pylint: disable=import-error

__license__ = 'GNU GPLv3'
__copyright__ = '2021, harmtemolder <mail at harmtemolder.com>'
__docformat__ = 'restructuredtext en'


COLUMNS = [{
    'name': 'column_percent_read',
    'label': 'Percent read column (float):',
    'tooltip': 'A “Floating point numbers” column to store the current\n'
               'percent read, with “Format for numbers” set to `{:.0%}`.',
    'type': 'float',
    'sidecar_property': ['percent_finished'],
    'transform': (lambda value: float(value))
}, {
    'name': 'column_percent_read_int',
    'label': 'Percent read column (int):',
    'tooltip': 'An “Integers” column to store the current percent read.',
    'type': 'int',
    'sidecar_property': ['percent_finished'],
    'transform': (lambda value: math.floor(float(value) * 100))
}, {
    'name': 'column_last_read_location',
    'label': 'Last read location column:',
    'tooltip': 'A regular “Text” column to store the location you last\n'
               'stopped reading at.',
    'type': 'text',
    'sidecar_property': ['last_xpointer'],
}, {
    'name': 'column_rating',
    'label': 'Rating column:',
    'tooltip': 'A “Rating” column to store your rating of the book,\n'
               'as entered on the book’s status page.',
    'type': 'rating',
    'sidecar_property': ['summary', 'rating'],
    'transform': (lambda value: value * 2),  # calibre uses a 10-point scale
}, {
    'name': 'column_review',
    'label': 'Review column:',
    'tooltip': 'A “Long text” column to store your review of the book,\n'
               'as entered on the book’s status page.',
    'type': 'comments',
    'sidecar_property': ['summary', 'note'],
}, {
    'name': 'column_status',
    'label': 'Reading status column:',
    'tooltip': 'A regular “Text” column to store the reading status of the\n'
               'book, as entered on the book status page (“Finished”,\n'
               '“Reading”, “On hold”).',
    'type': 'text',
    'sidecar_property': ['summary', 'status'],
}, {
    'name': 'column_date_status_modified',
    'label': 'Status modified date column:',
    'tooltip': 'A “Date” column to store the date on which the book’s status\n'
               'was last modified. (This is probably the date on which you\n'
               'marked it as read.)',
    'type': 'datetime',
    'sidecar_property': ['summary', 'modified'],
}, {
    'name': 'column_bookmarks',
    'label': 'Bookmarks column',
    'tooltip': 'A “Long text” column to store your bookmarks.',
    'type': 'comments',
    'sidecar_property': ['bookmarks'],
    'transform': clean_bookmarks,
}, {
# Ignore the sidecar's `highlight` property, because highlights are part of
# `bookmarks` as well
#     'name': 'column_highlights',
#     'label': 'Highlights column',
#     'tooltip': 'A “Long text” column to store your highlights.',
#     'type': 'comments',
#     'sidecar_property': ['highlight'],
#     'transform': clean_highlights,
# }, {
    'name': 'column_md5',
    'label': 'MD5 hash column:',
    'tooltip': 'A regular “Text” column to store the MD5 hash KOReader uses\n'
               'to sync progress to a KOReader Sync Server. (“Progress sync”\n'
               'in the KOReader app.) This might allow for syncing progress\n'
               'to calibre without having to connect your KOReader device,\n'
               'in the future.',
    'type': 'text',
    'sidecar_property': ['partial_md5_checksum'],
}, {
    'name': 'column_sidecar',
    'label': 'Raw sidecar column:',
    'tooltip': 'A “Long text” column to store the raw contents of the\n'
               'metadata sidecar, with “Interpret this column as” set to\n'
               '“Plain text”.',
    'type': 'comments',
    'sidecar_property': [],  # `[]` gives the entire sidecar dict
    'transform': (lambda value: json.dumps(value, indent=2)),
}]

CONFIG = JSONConfig(os.path.join('plugins', 'KOReader Sync.json'))
for column in COLUMNS:
    CONFIG.defaults[column['name']] = ''

if numeric_version >= (5, 5, 0):
    module_debug_print = partial(root_debug_print, ' koreader:config:', sep='')
else:
    module_debug_print = partial(root_debug_print, 'koreader:config:')


class ConfigWidget(QWidget):  # https://doc.qt.io/qt-5/qwidget.html
    def __init__(self, plugin_action):
        QWidget.__init__(self)
        debug_print = partial(module_debug_print, 'ConfigWidget:__init__:')
        debug_print('start')
        self.action = plugin_action

        # Set up main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add icon and title
        title_layout = TitleLayout(
            self, 'images/icon.png', 'Configure {}'.format(self.action.version))
        layout.addLayout(title_layout)

        # Add custom column dropdowns
        custom_columns_layout = CustomColumnsLayout(self)
        layout.addLayout(custom_columns_layout)

    def save_settings(self):
        debug_print = partial(module_debug_print,
                              'ConfigWidget:save_settings:')
        debug_print('old CONFIG = ', CONFIG)

        for column in COLUMNS:
            CONFIG[column['name']] = column['combo'].get_selected_column()

        debug_print('new CONFIG = ', CONFIG)


class TitleLayout(QHBoxLayout):
    """A sub-layout to the main layout used in ConfigWidget that contains an
    icon and title.
    """

    def __init__(self, parent, icon, title):
        QHBoxLayout.__init__(self)

        # Add icon
        icon_label = QLabel(parent)
        pixmap = QPixmap()
        pixmap.loadFromData(get_resources(icon))  # pylint: disable=undefined-variable
        icon_label.setPixmap(pixmap)
        icon_label.setMaximumSize(64, 64)
        icon_label.setScaledContents(True)
        self.addWidget(icon_label)

        # Add title
        title_label = QLabel('<h2>{}</h2>'.format(title), parent)
        self.addWidget(title_label)

        # Add empty space
        self.addStretch()

        # Add Readme hyperlink
        readme_label = QLabel('<a href="#">Readme</a>', parent)
        readme_label.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        readme_label.linkActivated.connect(parent.action.show_readme)
        self.addWidget(readme_label)

        # Add About hyperlink
        about_label = QLabel('<a href="#">About</a>', parent)
        about_label.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        about_label.linkActivated.connect(parent.action.show_about)
        self.addWidget(about_label)


class CustomColumnsLayout(QGridLayout):
    """A sub-layout to the main layout used in ConfigWidget that contains a
    grid of dropdowns for the mapping from KOReader metadata properties to
    calibre’s custom columns.
    """

    def __init__(self, parent):
        QGridLayout.__init__(self)
        self.action = parent.action
        row = 1

        # Get available columns per type
        available_columns = {
            'comments': self.get_custom_columns(['comments']),
            'datetime': self.get_custom_columns(['datetime']),
            'float': self.get_custom_columns(['float']),
            'int': self.get_custom_columns(['int']),
            'rating': self.get_rating_columns(),  # Includes built-in
            'text': self.get_custom_columns(['text']),
        }

        # Add custom column dropdowns
        for column in COLUMNS:
            label = QLabel(column['label'], parent)
            label.setToolTip(column['tooltip'])
            column['combo'] = CustomColumnComboBox(
                parent,
                available_columns[column['type']],
                CONFIG[column['name']])
            label.setBuddy(column['combo'])
            self.addWidget(label, row, 1, Qt.AlignRight)
            self.addWidget(column['combo'], row, 2, 1, 2)
            row += 1

    def get_custom_columns(self, column_types):
        custom_columns = self.action.gui.library_view.model().custom_columns
        available_columns = {}

        for key, column in custom_columns.items():
            type_ = column['datatype']
            if type_ in column_types and not column['is_multiple']:
                available_columns[key] = column

        return available_columns

    def get_rating_columns(self):
        rating_columns = self.get_custom_columns(['rating'])

        # Add built-in rating column as well
        rating_column_name = self.action.gui.library_view.model().orig_headers[
            'rating']
        rating_columns['rating'] = {'name': rating_column_name}

        return rating_columns


class CustomColumnComboBox(QComboBox):
    def __init__(self, parent, custom_columns={}, selected_column=''):
        QComboBox.__init__(self, parent)
        self.populate_combo(custom_columns, selected_column)

    def populate_combo(self, custom_columns, selected_column):
        self.clear()
        self.column_names = ['']
        self.addItem('do not sync')
        selected_idx = 0

        for key in sorted(custom_columns.keys()):
            self.column_names.append(key)
            display_name = '{} ({})'.format(custom_columns[key]['name'], key)
            self.addItem(display_name)
            if key == selected_column:
                selected_idx = len(self.column_names) - 1

        self.setCurrentIndex(selected_idx)

    def get_selected_column(self):
        return self.column_names[self.currentIndex()]
