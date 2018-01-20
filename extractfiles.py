#!/usr/bin/env python
import argparse
import mimetypes
import os
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

    source_mimetypes = []
    if os.path.isfile('.source_mimetypes'):
        with open('.source_mimetypes', 'r') as f:
            source_mimetypes = f.read().split()

    denied_mimetypes = []
    if os.path.isfile('.denied_mimetypes'):
        with open('.denied_mimetypes', 'r') as f:
            denied_mimetypes = f.read().split()

    source_paths_by_type = {}
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
                    with open('.source_mimetypes', 'a') as f:
                        f.write(mimetype + '\n')
                    source_mimetypes.append(mimetype)
                    source_paths.append(source_path)
                else:
                    with open('.denied_mimetypes', 'a') as f:
                        f.write(mimetype + '\n')
                    denied_mimetypes.append(mimetype)
            elif not mimetype:
                print '%r no mimetype guessed' % (source_path)

    all_files = []
    [all_files.extend(x) for x in source_paths_by_type.values()]
    for main_type, source_paths in source_paths_by_type.items():
        if source_paths:
            main_type_path = os.path.join(destination_abspath, main_type)
            if not os.path.isdir(main_type_path):
                os.mkdir(main_type_path)

            for source_path in source_paths:
                print '%d files to go' % (len(all_files))
                all_files.remove(source_path)
                dirname = os.path.dirname(source_path)
                base_path = os.path.basename(dirname)
                if not os.path.isdir(os.path.join(main_type_path, base_path)):
                    os.mkdir(os.path.join(main_type_path, base_path))
                filename = os.path.basename(source_path)
                destination_path = os.path.join(main_type_path, base_path, filename)
                if os.path.isfile(destination_path):
                    print '%r already exists at %r' % (source_path, destination_path)
                else:
                    print 'copying  %r to %r' % (source_path, destination_path)
                    shutil.copyfile(source_path, destination_path)


if __name__ == '__main__':
    main()
