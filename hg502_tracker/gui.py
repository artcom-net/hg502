import sys
from pathlib import Path

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)

from hg502_tracker import __app_name__

UI_DIR = 'ui'


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller.

    PyInstaller creates a temp folder and stores path in _MEIPASS.

    :type relative_path: str
    :rtype: str
    """
    if hasattr(sys, '_MEIPASS'):
        return str(Path(sys._MEIPASS).joinpath(relative_path))
    return str(Path('..').joinpath(relative_path))


class _UILoader(object):
    """The mixin class implements the loading of GUI parameters from *.ui."""

    _UI_FILE = None

    def __init__(self):
        """Initializes an instance."""
        uic.loadUi(
            Path(get_resource_path(UI_DIR)).joinpath(self._UI_FILE), self
        )


class _AboutWindow(QMainWindow, _UILoader):
    """About window class."""

    _UI_FILE = 'about_window.ui'

    def __init__(self):
        """Initializes an instance."""
        super(_AboutWindow, self).__init__()


class HG502GUI(QMainWindow, _UILoader):
    """Class of the main interface window."""

    _UI_FILE = 'main_window.ui'

    def __init__(self):
        """Initializes an instance."""
        super(HG502GUI, self).__init__()
        self.setWindowTitle(__app_name__)

        self.is_enabled_widgets = False
        self._about = _AboutWindow()

        self._status_label = QLabel()
        self._status_bar.addWidget(self._status_label)

        self._action_about.triggered.connect(self._show_about)
        self._search_button.clicked.connect(self._search_handler)
        self._items_tab.currentChanged.connect(self._change_tab_handler)

        self.set_widgets_status('disable')

    def _get_list_widgets(self):
        """Returns all QListWidget from the current tab."""
        return self._items_tab.currentWidget().findChildren(QListWidget)

    def _change_tab_handler(self):
        """Scrolls up when the tab is switched."""
        for list_w in self._get_list_widgets():
            list_w.scrollToTop()

    def _show_about(self):
        """Shows the about window."""
        self._about.show()

    def closeEvent(self, *args, **kwargs):
        """Closes the about window if the user has closed the main window."""
        if self._about.isVisible():
            self._about.close()

    def set_about_data(
        self, app_name, version, _license, author, author_email, home_page
    ):
        """Sets the values for the QLabel of the about window.

        :type app_name: str
        :type version: str
        :type _license: str
        :type author: str
        :type author_email: str
        :type home_page: str
        """
        self._about._app_name_label.setText(app_name)
        self._about._version_value.setText(version)
        self._about._license_value.setText(_license)
        self._about._author_value.setText(author)
        self._about._author_email_value.setText(author_email)
        self._about._home_page_value.setText(home_page)

    def action_handler_register(self, action, func):
        """Registers a handler for an action.

        :type action: str
        :type func: function
        """
        _action = getattr(self, action)
        _action.triggered.connect(func)

    def clicked_handler_register(self, widget, func):
        """Registers a handler for a clicked event.

        :type widget: str
        :type func: function
        """
        obj = getattr(self, widget)
        obj.clicked.connect(func)

    def show_open_folder_dialog(self, title, directory):
        """Displays the directory selection dialog.

        :param title: Window title
        :type title: str
        :param directory: Directory to open
        :type directory: str
        :return: Path to the directory
        :rtype: str
        """
        return QFileDialog.getExistingDirectory(
            self, title, directory=directory
        )

    @staticmethod
    def _clear_selected(list_widget):
        """Resets selection from QListWidget elements.

        :type list_widget: QListWidget
        """
        for item in list_widget.selectedItems():
            item.setSelected(False)

    def _search_handler(self):
        """Handler for the search button click event."""
        search_text = self._search_line.text().strip()
        if not search_text:
            return None
        for list_w in self._get_list_widgets():
            items = list_w.findItems(search_text, QtCore.Qt.MatchContains)
            self._clear_selected(list_w)
            list_w.setSelectionMode(QAbstractItemView.MultiSelection)
            if items:
                for item in items:
                    item.setSelected(True)
                    list_w.scrollToItem(
                        item, QAbstractItemView.PositionAtCenter
                    )
            list_w.setSelectionMode(QAbstractItemView.SingleSelection)

    def set_widgets_status(self, status):
        """Enables / disables widgets.

        :param status: 'enabled' or 'disabled'
        :type status: str
        """
        is_enable = True if status == 'enable' else False
        for widget in (
            self._stat_table,
            self._refresh_button,
            self._search_line,
            self._search_button,
            self._items_tab,
        ):
            widget.setEnabled(is_enable)
        self.is_enabled_widgets = is_enable

    def fill_stat_table(self, data):
        """Fills in the statistics table.

        :param data: A list of three elements where each element is 4 long and
        is a table row.
        :type data: iterable
        """
        row = 0
        for row_data in data:
            column = 0
            for value in row_data:
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self._stat_table.setItem(row, column, item)
                column += 1
            row += 1

    @staticmethod
    def _fill_items_list(w_list, data):
        """Fills the QListWidget with data from `data`.

        :type w_list: QListWidget
        :type data: list
        """
        w_list.clear()
        for value in data:
            w_list.addItem(value)
        w_list.scrollToTop()

    def fill_all_items_list(self, found, remaining):
        """Fills the QListWidget of the `All` tab.

        :type found: list
        :type remaining: list
        """
        self._fill_items_list(self._all_list_found, found)
        self._fill_items_list(self._all_list_remaining, remaining)

    def fill_set_items_list(self, found, remaining):
        """Fills the QListWidget of the `Set's` tab.

        :type found: list
        :type remaining: list
        """
        self._fill_items_list(self._set_list_found, found)
        self._fill_items_list(self._set_list_remaining, remaining)

    def fill_unique_items_list(self, found, remaining):
        """Fills the QListWidget of the `Unique` tab.

        :type found: list
        :type remaining: list
        """
        self._fill_items_list(self._unique_list_found, found)
        self._fill_items_list(self._unique_list_remaining, remaining)

    @staticmethod
    def _init_message(msg_type, title, short_text, info_text):
        """Initializes message.

        :type msg_type: QMessageBox.Information | QMessageBox.Critical
        :type title: str
        :type short_text: str
        :type info_text: str
        :rtype: QMessageBox
        """
        msg = QMessageBox()
        msg.setIcon(msg_type)
        msg.setText(short_text)
        msg.setInformativeText(info_text)
        msg.setWindowTitle(title)
        return msg

    def show_info_message(self, title, short_text, info_text):
        """Displays an informational message.

        :type title: str
        :type short_text: str
        :type info_text: str
        """
        msg = self._init_message(
            QMessageBox.Information, title, short_text, info_text
        )
        msg.exec_()

    def show_error_message(self, title, short_text, error_text):
        """Displays an error message.

        :type title: str
        :type short_text: str
        :type error_text: str
        """
        msg = self._init_message(
            QMessageBox.Critical, title, short_text, error_text
        )
        msg.exec_()

    def set_status_bar_text(self, text):
        """Sets the value of the status bar.

        :type text: str
        """
        self._status_label.setText(text)
