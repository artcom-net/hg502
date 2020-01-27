import sys
from pathlib import Path

import qdarkstyle

from hg502_tracker import (
    __app_name__,
    __author__,
    __author_email__,
    __home_page__,
    __license__,
    __version__,
)
from hg502_tracker.hg502 import FileParseError


class HG502App(object):
    """This class is a presenter. Manages the backend and GUI."""

    def __init__(self, gui, backend, q_app):
        """Initializes an instance.

        :type gui: src.gui.HG502GUI
        :type backend: src.hg502_tracker.HG502
        :type q_app: QApplication
        """
        self._gui = gui
        self._backend = backend
        self._q_app = q_app
        self._home_path = Path().home()
        self._settings_path = self._home_path.joinpath('.hg502')
        self._save_path = None

        self._q_app.setStyleSheet(qdarkstyle.load_stylesheet())
        self._gui.set_about_data(
            __app_name__,
            __version__,
            __license__,
            __author__,
            __author_email__,
            f'<html><head/><body><p>'
            f'<a href="{__home_page__}">'
            f'<span style=" text-decoration: underline; color:#ffffff;">'
            f'{__home_page__}</span></a></p></body></html>',
        )
        self._gui.action_handler_register(
            '_action_folder', self._open_folder_handler
        )
        self._gui.action_handler_register('_action_exit', self._exit_handler)
        self._gui.clicked_handler_register(
            '_refresh_button', self._refresh_handler
        )

        if self._settings_path.exists():
            self._save_path = self._settings_path.read_text()
            self._show_stat()

    @staticmethod
    def _prepare_stat(stat_dict):
        """Prepares statistics data for the GUI.

        :type stat_dict: dict
        :rtype: dict
        """
        stat_fields = ('total_items', 'total_found', 'total_remaining')
        stat = [
            str(stat_dict[field])
            for field in stat_dict
            if field in stat_fields
        ]
        stat.append(f'{stat_dict["progress"]:.2f}%')
        return stat

    def _show_stat(self):
        """Displays statistics in a GUI.

        :rtype: bool
        """
        if not self._push_stat():
            return False
        self._gui.set_status_bar_text(f'Current folder: {self._save_path}')
        if not self._gui.is_enabled_widgets:
            self._gui.set_widgets_status('enable')
        return True

    def _push_stat(self):
        """Fills widgets with necessary data.

        :rtype: bool
        """
        try:
            total_stat, set_stat, unique_stat = self._backend.get_hg502_stat(
                self._save_path
            )
        except FileNotFoundError:
            self._gui.show_info_message(
                'Info',
                'Files not found',
                f'{self._save_path} does not contain Diablo 2 files',
            )
            return False
        except FileParseError as err:
            self._gui.show_error_message('Error', 'File parse error', f'{err}')
            return False

        stats = []
        for stat_dict in (set_stat, unique_stat, total_stat):
            stats.append(self._prepare_stat(stat_dict))
        self._gui.fill_stat_table(stats)
        self._gui.fill_set_items_list(
            set_stat['found_items'], set_stat['remaining_items']
        )
        self._gui.fill_unique_items_list(
            unique_stat['found_items'], unique_stat['remaining_items']
        )

        all_found = set_stat['found_items'].copy()
        all_found.extend(unique_stat['found_items'].copy())
        all_remaining = set_stat['remaining_items'].copy()
        all_remaining.extend(unique_stat['remaining_items'].copy())

        self._gui.fill_all_items_list(all_found, all_remaining)

        return True

    def _open_folder_handler(self):
        """`Folder...` button event handler.

        Displays the explorer for directory selection and calls _show_stat
        if input was received.
        """
        folder_path = self._gui.show_open_folder_dialog(
            'Diablo 2 save folder', directory=str(self._home_path)
        )
        if folder_path:
            self._save_path = folder_path
            if self._show_stat():
                self._settings_path.write_text(self._save_path)

    def _refresh_handler(self):
        """`Refresh` button event handler."""
        self._push_stat()

    def _exit_handler(self):
        """`Exit` button event handler."""
        self._q_app.quit()

    def run(self):
        """Displays GUI."""
        self._gui.show()
        sys.exit(self._q_app.exec_())
