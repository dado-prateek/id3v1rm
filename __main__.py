__author__ = 'Borg'

import os
import sys
import logging
import argparse
from collections import namedtuple

logging.basicConfig(format='%(asctime)16s %(levelname)6s %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

PROGRESS_BAR_LENGTH = 35
TAGS_TEMPLATE = '''Found tags
Header: {header}
Song Title: {title}
Artist: {artist}
Album: {album}
Year: {year}
Comment: {comment}
Genre: {genre}'''


def find_files(path, recursive=False):
    if os.path.isdir(path):
        log.info('Searching for mp3 files in {}{}'.format(args.path, ' recursively' if args.recursive else ''))
        fns = ffiles(path, recursive)
    else:
        fns = [path]
    return fns


def ffiles(path, recursive=False):
    fns = []
    for fn in os.listdir(path):
        try:
            fp = os.path.join(path, fn)
            if os.path.isdir(fp) and recursive:
                fns.extend(ffiles(fp, recursive))
            elif fn[-4:] == '.mp3':
                fns.append(os.path.join(path, fn))
                log.debug('Add {}'.format(fn))
        except PermissionError as e:
            log.debug(e)
    return fns


def draw_progress_bar(total, completed):
    ratio = completed / total
    fill_len = int(ratio * PROGRESS_BAR_LENGTH)
    fill = '#' * fill_len
    white_space = ' ' * (PROGRESS_BAR_LENGTH - fill_len)
    sys.stdout.write("\rProcessing files [{}{}] ({}/{})".format(fill, white_space, completed, total))
    if total == completed:
        print()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Remove ID3V1 tags')
    parser.add_argument('path', type=str, help='path to file or dir')
    parser.add_argument('-r', '--recursive', help='find files in sub dirs', action="store_true")
    parser.add_argument('-v', '--verbose', help='output debug information', action="store_true")
    parser.add_argument('-n', '--dry-run', help='perform trial run without modifying files', action="store_true")
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    Fields = namedtuple('Fields', ['header', 'title', 'artist', 'album', 'year', 'comment', 'genre'])
    field_lens = Fields(header=3, title=30, artist=30, album=30, year=4, comment=30, genre=1)

    file_names = find_files(args.path, recursive=args.recursive)
    files_count = len(file_names)
    log.info('Found {} files'.format(files_count))

    truncate_count = 0
    process_count = 0
    for fn in file_names:
        process_count += 1
        log.debug('Processing file {}'.format(fn))
        size = os.path.getsize(fn)
        log.debug('File size: {}'.format(size))
        if size > 0:
            start_pos = size - sum(field_lens)
        else:
            log.debug('Skipping zero size file: {}'.format(fn))
            continue

        with open(fn, 'rb') as mp3file:
            mp3file.seek(start_pos)
            tags = Fields._make([mp3file.read(x) for x in field_lens])

        if tags.header == b'TAG':
            log.debug(TAGS_TEMPLATE.format(**tags._asdict()))
            log.debug('Removing')
            truncate_count += 1
            if not args.dry_run:
                log.debug('Truncating file {}'.format(fn))
                try:
                    with open(fn, 'ab') as file:
                        file.seek(start_pos)
                        file.truncate()
                except PermissionError as e:
                    log.info(e)
        else:
            log.debug('No tags found in {}'.format(fn))

        draw_progress_bar(files_count, process_count)

    log.info('Total files processed: {}'.format(truncate_count))
    space = int(truncate_count * 128 / 1000)
    log.info('Total space saved: {} KB'.format(space))

