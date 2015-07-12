__author__ = 'Borg'

import logging
import os
import argparse
from collections import namedtuple

logging.basicConfig(format='%(asctime)16s %(levelname)6s %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

found_tags_msg = '''Found tags
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
    log.info('Found {} files'.format(len(fns)))
    return fns


def ffiles(path, recursive=False):
    fns = []
    for fn in os.listdir(path):
        try:
            fp = os.path.join(path, fn)
            if os.path.isdir(fp) and recursive:
                fns.extend(ffiles(fp, recursive))
            elif fn[-4:] == '.mp3':
                fns.append(os.path.join(path , fn))
                log.debug('Add {}'.format(fn))
        except PermissionError as e:
            log.debug(e)
    return fns


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Remove ID3V1 tags')
    parser.add_argument('path', type=str, help='path to file or dir')
    parser.add_argument('-r', '--recursive', help='find files in sub folder', action="store_true")
    parser.add_argument('-v', '--verbose', help='debug output', action="store_true")
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    Fields = namedtuple('Fields', ['header', 'title', 'artist', 'album', 'year', 'comment', 'genre'])
    field_lens = Fields(header=3, title=30, artist=30, album=30, year=4, comment=30, genre=1)

    file_names = find_files(args.path, recursive=args.recursive)

    for fn in file_names:
        log.debug('Processing file {}'.format(fn))
        size = os.path.getsize(fn)
        if size > 0:
            start_pos = size - sum(field_lens)
        else:
            log.debug('Skipping zero size file: {}'.format(fn))
            continue

        with open(fn, 'rb') as mp3file:
            mp3file.seek(start_pos)
            tags = Fields._make([mp3file.read(x) for x in field_lens])

        if tags.header == b'TAG':
            log.debug(found_tags_msg.format(**tags._asdict()))
            log.debug('Removing')
            with open(fn, 'wb') as file:
                file.seek(start_pos)
                file.truncate()
        else:
            log.debug('No tags found in {}'.format(fn))

    log.info('Total files processed: {}'.format(len(file_names)))

