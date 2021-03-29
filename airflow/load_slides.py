#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import shutil

logger = logging.getLogger()


def main(src_dir, dest_dir):
    for filename in os.listdir(src_dir):
        full_path = os.path.join(src_dir, filename)
        if not os.path.isdir(full_path):
            basename, ext = os.path.splitext(filename)
            if ext == '.mrxs':
                load_mrxs(full_path, dest_dir)
            else:
                shutil.copy(full_path, dest_dir)


def load_mrxs(filename, dest_dir):
    base_dir, _ = os.path.splitext(filename)
    mrxs_dest_dir = os.path.join(
        dest_dir,
        os.path.splitext(os.path.basename(filename))[0])
    os.mkdir(mrxs_dest_dir)
    for f in os.listdir(base_dir):
        shutil.copy(os.path.join(base_dir, f), mrxs_dest_dir)

    shutil.copy(filename, dest_dir)


#  def copytree(src, dst, symlinks=False, ignore=None):
#      for item in os.listdir(src):
#
#          s = os.path.join(src, item)
#          d = os.path.join(dst, item)
#          if os.path.isdir(s):
#              logger.debug('copytree %s -> %s', s, d)
#              shutil.copytree(s, d, symlinks, ignore)
#          else:
#              logger.debug('copy %s -> %s', s, d)
#              shutil.copy2(s, d)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load slides')
    parser.add_argument('src_dir')
    parser.add_argument('dest_dir')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    main(args.src_dir, args.dest_dir)
