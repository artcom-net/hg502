import json
from pathlib import Path

import pytest

from hg502_tracker.hg502 import HG502

SAVE_PATH = 'data'
ITEMS_DICT = {0: 'Test0', 1: 'Test1', 2: 'Test2', 3: 'Test3'}
USER_ITEMS_DICT = {4: 'Test4', 5: 'Test5'}


@pytest.fixture(scope='module')
def hg502():
    return HG502()


@pytest.fixture(scope='module')
def hg502_expected(hg502):
    set_stat = None
    unique_stat = None
    total_stat = None
    for path in Path(SAVE_PATH).glob('*.json'):
        if path.stem == 'total_stat':
            total_stat = json.loads(path.open('r').read())
        elif path.stem == 'set_stat':
            set_stat = json.loads(path.open('r').read())
        elif path.stem == 'unique_stat':
            unique_stat = json.loads(path.open('r').read())
    return hg502, total_stat, set_stat, unique_stat


def test_hg502_constructor(hg502):
    assert hg502._set_dict
    assert hg502._unique_dict
    assert len(hg502._set_dict) == 127
    assert len(hg502._unique_dict) == 375

    for quest_item_id in hg502._QUESTS_UNIQUE:
        assert quest_item_id not in hg502._unique_dict
    for die_facet_id, level_up_facet_id in hg502._FACET_PAIRS:
        assert die_facet_id in hg502._unique_dict
        assert level_up_facet_id not in hg502._unique_dict

    assert hg502._save_path is None
    assert not hg502._user_set_items
    assert not hg502._user_unique_items
    assert isinstance(hg502._user_set_items, dict)
    assert isinstance(hg502._user_unique_items, dict)


def test_hg502_get_stat_dict(hg502):
    stat_dict = hg502._get_stat_dict()
    assert stat_dict
    assert isinstance(stat_dict, dict)
    assert stat_dict['total_items'] == 0
    assert stat_dict['total_found'] == 0
    assert stat_dict['total_remaining'] == 0
    assert stat_dict['progress'] == 0.0
    assert isinstance(stat_dict['found_items'], list)
    assert isinstance(stat_dict['remaining_items'], list)


@pytest.mark.parametrize(
    'total,part,expected',
    ((150, 15, 10.0), (100, 100, 100.0), (502, 348, 69.32270916334662)),
)
def test_hg502_calc_percentage(hg502, total, part, expected):
    assert hg502._calc_percentage(total, part) == expected


def test_hg502_get_hg502_stat(hg502_expected):
    hg502, total_stat_exp, set_stat_exp, unique_stat_exp = hg502_expected
    total_stat, set_stat, unique_stat = hg502.get_hg502_stat(SAVE_PATH)
    assert total_stat == total_stat_exp
    assert set_stat == set_stat_exp
    assert unique_stat == unique_stat_exp


@pytest.mark.parametrize(
    'stat_dict,items_dict,user_items_dict,expected',
    (
        (
            {
                'total_items': 0,
                'total_found': 0,
                'total_remaining': 0,
                'progress': 0.0,
                'found_items': [],
                'remaining_items': [],
            },
            ITEMS_DICT,
            USER_ITEMS_DICT,
            {
                'total_items': 4,
                'total_found': 2,
                'total_remaining': 2,
                'progress': 50.0,
                'found_items': ['Test4', 'Test5'],
                'remaining_items': [],
            },
        ),
    ),
)
def test_hg502_get_common_stat(
    hg502, stat_dict, items_dict, user_items_dict, expected
):
    hg502._get_common_stat(stat_dict, items_dict, user_items_dict)
    assert stat_dict == expected


@pytest.mark.parametrize(
    'items_dict,user_items_dict,expected',
    ((ITEMS_DICT, USER_ITEMS_DICT, {0, 1, 2, 3}),),
)
def test_hg502_get_remaining_ids(hg502, items_dict, user_items_dict, expected):
    assert hg502._get_remaining_ids(items_dict, user_items_dict) == expected


def test_hg502_load_user_items(hg502):
    hg502._load_user_items(SAVE_PATH)
    assert hg502._save_path == SAVE_PATH
    assert hg502._user_set_items
    assert hg502._user_unique_items


def test_hg502_load_user_items_invalid_path(hg502):
    with pytest.raises(FileNotFoundError):
        hg502._load_user_items('.')


@pytest.mark.parametrize(
    'facet_id,expected', ((392, True), (399, True), (391, False), (400, False))
)
def test_hg502_is_facet(hg502, facet_id, expected):
    assert hg502._is_facet(facet_id) is expected


@pytest.mark.parametrize(
    'facet_id,expected', ((392, 392), (397, 393), (399, 395), (394, 394))
)
def test_hg502_get_die_facet_id(hg502, facet_id, expected):
    assert hg502._get_die_facet_id(facet_id) == expected


@pytest.mark.parametrize(
    'facet_id,expected',
    ((392, 'Lightning'), (398, 'Fire'), (399, 'Poison'), (393, 'Cold')),
)
def test_hg502_get_facet_suffix(hg502, facet_id, expected):
    assert hg502._get_facet_suffix(facet_id) == expected
