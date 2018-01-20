#!/usr/bin/env python
import argparse
import os
import mimetypes
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='path to start the recursive search')
    parser.add_argument('destination', help='path where the extracted files will go')
    args = parser.parse_args()

    source_abspath = os.path.abspath(args.source)
    destination_abspath = os.path.abspath(args.destination)

    assert os.path.isdir(source_abspath), source_abspath
    assert os.path.isdir(destination_abspath), destination_abspath
    assert not os.path.samefile(source_abspath, destination_abspath), (source_abspath, destination_abspath)

    source_paths_by_type = {}
    source_mimetypes = []
    denied_mimetypes = []
    for dirpath, dirnames, filenames in os.walk(source_abspath):
        for filename in filenames:
            source_path = os.path.join(dirpath, filename)
            mimetype = mimetypes.guess_type(source_path)[0]
            if mimetype:
                main_type = mimetype.split('/')[0]
                source_paths = source_paths_by_type.setdefault(main_type, [])
            if mimetype and mimetype in source_mimetypes:
                source_paths.append(source_path)
            elif mimetype and mimetype not in source_mimetypes and mimetype not in denied_mimetypes:
                print '%r with mimetype %r' % (source_path, mimetype)
                user_input = raw_input('include files with mimetype %r? [y/N]' % (mimetype))
                if user_input.lower() == 'y':
                    source_mimetypes.append(mimetype)
                    source_paths.append(source_path)
                else:
                    denied_mimetypes.append(mimetype)
            elif not mimetype:
                print '%r no mimetype guessed' % (source_path)

    for main_type, source_paths in source_paths_by_type.items():
        if source_paths:
            main_type_path = os.path.join(destination_abspath, main_type)
            if not os.path.isdir(main_type_path):
                os.mkdir(main_type_path)

            for source_path in source_paths:
                filename = os.path.basename(source_path)
                destination_path = os.path.join(main_type_path, filename)
                assert not os.path.exists(destination_path), destination_path
                shutil.copyfile(source_path, destination_path)


if __name__ == '__main__':
    main()
