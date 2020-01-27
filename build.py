import os
import site
import sys
from pathlib import Path
from tarfile import TarFile
from zipfile import ZIP_DEFLATED, ZipFile

import PyInstaller.__main__

from hg502_tracker import __app_name__, __version__

BUILD_DIR = 'build'
DIST_DIR = 'dist'
UI_DIR = 'ui'
STATIC_DIR = 'static'
ICON_NAME = 'icon.ico'
SCRIPT_PATH = 'hg502_tracker/main.py'


def retrieve_file_paths(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(Path(root).joinpath(file))

    return file_list


def build_package():
    build_path = Path(BUILD_DIR)
    build_path.mkdir(exist_ok=True)
    work_path = build_path.joinpath('build')
    build_dist_path = build_path.joinpath('dist')

    _, site_packages_path = site.getsitepackages()
    items_data = 'd2lib/items_data'
    items_data_path = Path(site_packages_path).joinpath(items_data)

    ui_path = Path(UI_DIR).absolute()
    static_path = Path(STATIC_DIR).absolute()
    icon_path = static_path.joinpath(ICON_NAME).absolute()

    path_sep = ';' if sys.platform == 'win32' else ':'

    _items_data = f'{items_data_path}{path_sep}{items_data}'
    ui_data = f'{ui_path}{path_sep}{UI_DIR}'
    static_data = f'{static_path}{path_sep}{STATIC_DIR}'

    PyInstaller.__main__.run(
        [
            '--clean',
            '--noconfirm',
            '--onedir',
            '--windowed',
            f'--name={__app_name__}',
            f'--workpath={work_path}',
            f'--distpath={build_dist_path}',
            f'--specpath={work_path}',
            f'--add-data={_items_data}',
            f'--add-data={ui_data}',
            f'--add-data={static_data}',
            f'--icon={icon_path}',
            SCRIPT_PATH,
        ]
    )

    file_list = retrieve_file_paths(build_dist_path.joinpath(__app_name__))
    out_file_name = '-'.join(
        (f'{__app_name__}', f'{__version__}', f'{sys.platform}',)
    )
    dist_path = Path(DIST_DIR)
    dist_path.mkdir(exist_ok=True)
    archive_path = dist_path.joinpath(f'{out_file_name}')

    if sys.platform == 'win32':
        zip_file = ZipFile(f'{archive_path}.zip', 'w', ZIP_DEFLATED)
        with zip_file:
            for file_path in file_list:
                zip_file.write(
                    file_path, arcname=file_path.relative_to(build_dist_path)
                )
    else:
        tar_file = TarFile.open(f'{archive_path}.tar.gz', 'w:gz')
        with tar_file:
            for file_path in file_list:
                tar_file.add(
                    file_path, arcname=file_path.relative_to(build_dist_path)
                )


if __name__ == '__main__':
    build_package()
