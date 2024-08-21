#!/usr/bin/env python
'''
generateimageindex
------------------
Author: Jake Gustafson

Generate a markdown file that shows all of the files with
{image_image_extensions}.
'''
import os
import sys


image_extensions = ['png', 'jpeg', 'jpg', 'jpe', 'bmp', 'gif']


def usage():
    print(__doc__.format(
        image_image_extensions=image_extensions,
    ))


def make_md_index(parent, name="readme.md", extensions=image_extensions):
    '''List images (see image_extensions)
    and put links to them in readme.md.

    Args:
        name (str, optional): Set the name of the markdown file that is
            generated (and *appended* in parent. The name "readme.md"
            (case insensitive) is most commonly the name of the file
            loaded automatically as the index when a folder is opened
            (such as on the GitHub web interface and when using
            VuePress).

    Returns:
        int: The number of images found.
    '''
    dst = os.path.join(parent, name)
    image_dot_exts = []
    images_count = 0
    new_count = 0
    lines = []
    print('# looking in "{}"'.format(parent))
    for extension in image_extensions:
        image_dot_exts.append("." + extension.lower())
    for sub in os.listdir(parent):
        subPath = os.path.join(parent, sub)
        if not os.path.isfile(subPath):
            continue
        no_ext, ext = os.path.splitext(sub)
        if ext.lower() not in image_dot_exts:
            continue
        line = "![{}]({})".format(no_ext, sub)
        lines.append(line)
        images_count += 1
    old_lines = []
    if os.path.isfile(dst):
        with open(dst, 'r') as f:
            old_lines = [line.rstrip() for line in f]
        print('* appending missing images to "{}" from "{}"'
              ''.format(dst, parent))
    else:
        print('* creating "{}"'.format(dst))
    print("  images_count={}".format(images_count))
    if len(lines) < 1:
        return 0

    with open(dst, 'w') as f:
        for line in lines:
            if line not in old_lines:
                f.write(line + "\n")
                new_count += 1
    print("  new_count={}".format(new_count))
    return images_count


def main():
    parents = []
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if not os.path.isdir(arg):
            usage()
            raise ValueError("{} is not a directory.")
        parents.append(arg)
    if len(parents) == 0:
        parents.append(os.path.realpath("."))
    for parent in parents:
        make_md_index(parent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
