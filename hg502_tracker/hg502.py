from pathlib import Path

from d2lib.errors import D2SFileParseError, ItemParseError, StashFileParseError
from d2lib.files import D2SFile, D2XFile, SSSFile
from d2lib.items_storage import ItemsDataStorage


class FileParseError(Exception):
    """Used in case of errors in parsing user files."""

    pass


class HG502(object):
    """This class retrieves user item data."""

    _QUESTS_UNIQUE = (123, 124, 125, 126, 127, 128, 4095)
    # (die_facet, level_up_facet)
    _FACET_LIGHT = (392, 396)
    _FACET_COLD = (393, 397)
    _FACET_FIRE = (394, 398)
    _FACET_POISON = (395, 399)
    _FACET_SUFFIXES = {
        _FACET_LIGHT: 'Lightning',
        _FACET_COLD: 'Cold',
        _FACET_FIRE: 'Fire',
        _FACET_POISON: 'Poison',
    }
    _FACET_PAIRS = (_FACET_LIGHT, _FACET_COLD, _FACET_FIRE, _FACET_POISON)

    def __init__(self):
        """Initializes an instance."""
        item_storage = ItemsDataStorage()
        self._set_dict = item_storage.get_set_dict()
        self._unique_dict = item_storage.get_unique_dict()

        for quest_item_id in self._QUESTS_UNIQUE:
            self._unique_dict.pop(quest_item_id)
        for _, level_up_facet_id in self._FACET_PAIRS:
            self._unique_dict.pop(level_up_facet_id)

        self._save_path = None
        self._user_set_items = {}
        self._user_unique_items = {}

    @staticmethod
    def _get_stat_dict():
        """Returns the prepared dictionary for statistics."""
        return {
            'total_items': 0,
            'total_found': 0,
            'total_remaining': 0,
            'progress': 0.0,
            'found_items': [],
            'remaining_items': [],
        }

    @staticmethod
    def _calc_percentage(total, part):
        """Calculates the percentage of part from total.

        :type total: int
        :type part: int
        :rtype: float
        """
        return 100 * (part / total)

    def get_hg502_stat(self, save_path):
        """Collects statistics for all types of items.

        :param save_path: Path to Diablo 2 save directory
        :type save_path: str
        :return: Three dictionaries that look like this:
        {
            'total_items': int,
            'total_found': int,
            'total_remaining': int,
            'progress': float,
            'found_items': list,
            'remaining_items': list
        }
        :rtype: tuple
        """
        self._user_set_items.clear()
        self._user_unique_items.clear()

        total_stat = self._get_stat_dict()
        set_stat = self._get_stat_dict()
        unique_stat = self._get_stat_dict()
        self._load_user_items(save_path)

        if self._user_set_items:
            self._get_set_stat(set_stat)
        if self._user_unique_items:
            self._get_unique_stat(unique_stat)

        for sum_field in ('total_items', 'total_found', 'total_remaining'):
            total_stat[sum_field] += (
                set_stat[sum_field] + unique_stat[sum_field]
            )

        total_stat['progress'] = self._calc_percentage(
            total_stat['total_items'], total_stat['total_found']
        )

        for sorted_field in ('found_items', 'remaining_items'):
            set_stat[sorted_field].sort()
            unique_stat[sorted_field].sort()

        return total_stat, set_stat, unique_stat

    def _get_common_stat(self, stat_dict, items_dict, user_items_dict):
        """Fills in the general statistics for each type.

        :param stat_dict: Dictionary which is filled with data
        :type stat_dict: dict
        :param items_dict: Dictionary containing all items
        :type items_dict: dict
        :param user_items_dict: Dictionary with user items
        :type user_items_dict: dict
        """
        items_dict_len = len(items_dict)
        user_items_len = len(user_items_dict)
        stat_dict['total_items'] = items_dict_len
        stat_dict['total_found'] = user_items_len
        stat_dict['total_remaining'] = items_dict_len - user_items_len
        stat_dict['progress'] = self._calc_percentage(
            items_dict_len, user_items_len
        )
        stat_dict['found_items'] = list(user_items_dict.values())

    @staticmethod
    def _get_remaining_ids(items_dict, user_items_dict):
        """Calculates which item IDs the user does not have.

        :param items_dict: Dictionary containing all items
        :type items_dict: dict
        :param user_items_dict:  Dictionary with user items
        :type user_items_dict: dict
        :rtype: set
        """
        return set(items_dict).difference(set(user_items_dict))

    def _get_set_stat(self, stat_dict):
        """Collects statistics on set's items.

        :param stat_dict: Dictionary which is filled with data
        :type stat_dict: dict
        """
        self._get_common_stat(stat_dict, self._set_dict, self._user_set_items)
        remaining_items = []
        for remaining_id in self._get_remaining_ids(
            self._set_dict, self._user_set_items
        ):
            remaining_items.append(self._set_dict.get(remaining_id))

        stat_dict['remaining_items'] = remaining_items

    def _get_unique_stat(self, stat_dict):
        """Collects statistics on unique items.

        :param stat_dict: Dictionary which is filled with data
        :type stat_dict: dict
        """
        self._get_common_stat(
            stat_dict, self._unique_dict, self._user_unique_items
        )
        remaining_items = []
        for remaining_id in self._get_remaining_ids(
            self._unique_dict, self._user_unique_items
        ):
            if self._is_facet(remaining_id):
                remaining_items.append(
                    f'{self._unique_dict.get(remaining_id)} '
                    f'{self._get_facet_suffix(remaining_id)}'
                )
            else:
                remaining_items.append(self._unique_dict.get(remaining_id))

        stat_dict['remaining_items'] = remaining_items

    def _load_user_items(self, save_path):
        """Retrieves data for user items such as set's items and unique items.

        Data is taken from .d2s, .d2s and .sss files where .d2x is a PlugY
        personal stash file.

        :param save_path: Path to Diablo 2 save directory
        :type save_path: str
        :raises FileParseError:
        """
        self._save_path = save_path
        d2s_files = []
        stash_files = []

        try:
            for path in Path(self._save_path).iterdir():
                if path.suffix == '.d2s':
                    d2s_files.append(D2SFile(str(path)))
                elif path.suffix == '.d2x':
                    stash_files.append(D2XFile(str(path)))
                elif path.suffix == '.sss':
                    stash_files.append(SSSFile(str(path)))
        except (D2SFileParseError, StashFileParseError, ItemParseError) as err:
            raise FileParseError(f'{path}: {err}')

        if not any((d2s_files, stash_files)):
            raise FileNotFoundError

        for d2s in d2s_files:
            if d2s.items:
                self._filter_items(d2s.items)
            if d2s.corpse_items:
                self._filter_items(d2s.corpse_items)
            if d2s.merc_items:
                self._filter_items(d2s.merc_items)

        for stash_file in stash_files:
            for page in stash_file.stash:
                self._filter_items(page['items'])

    def _is_facet(self, item_id):
        """Returns True if the ID belongs to Rainbow facet otherwise False.

        :type item_id: int
        :rtype: bool
        """
        for pair in self._FACET_PAIRS:
            if item_id in pair:
                return True
        return False

    def _get_die_facet_id(self, facet_id):
        """Returns the ID of die facet by its pair.

        :type facet_id:
        :rtype: int
        """
        for pair in self._FACET_PAIRS:
            if facet_id in pair:
                return pair[0]

    def _get_facet_suffix(self, facet_id):
        """Returns an appropriate suffix by facet ID.

        :type facet_id: int
        :rtype: str
        """
        for pair, suffix in self._FACET_SUFFIXES.items():
            if facet_id in pair:
                return suffix

    def _filter_items(self, items):
        """Filters the desired items.

        For the HG 502 challenge, need set's and unique items. Rainbow facets
        count as four.

        :type items: list
        """
        for item in items:
            if item.is_set and item.set_id not in self._user_set_items:
                self._user_set_items[item.set_id] = item.name
            elif (
                item.is_unique
                and item.unique_id not in self._QUESTS_UNIQUE  # noqa
                and item.unique_id not in self._user_unique_items  # noqa
            ):
                if self._is_facet(item.unique_id):
                    die_facet_id = self._get_die_facet_id(item.unique_id)
                    if die_facet_id in self._user_unique_items:
                        continue
                    facet_name = (
                        f'{item.name} {self._get_facet_suffix(die_facet_id)}'
                    )
                    self._user_unique_items[die_facet_id] = facet_name
                    continue
                self._user_unique_items[item.unique_id] = item.name

            if item.socketed_items:
                self._filter_items(item.socketed_items)
