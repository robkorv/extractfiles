#!/usr/bin/env python3
import argparse
import mimetypes
import os
import shutil
import urllib
import subprocess
import shlex
import pathlib
import imghdr


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

    included_mimetypes = []
    if os.path.isfile('.included_mimetypes'):
        with open('.included_mimetypes', 'r') as f:
            included_mimetypes = [line.strip() for line in f]

    excluded_mimetypes = []
    if os.path.isfile('.excluded_mimetypes'):
        with open('.excluded_mimetypes', 'r') as f:
            excluded_mimetypes = [line.strip() for line in f]

    included_paths = []
    if os.path.isfile('.included_paths'):
        with open('.included_paths', 'r') as f:
            included_paths = [line.strip() for line in f]

    excluded_paths = []
    if os.path.isfile('.excluded_paths'):
        with open('.excluded_paths', 'r') as f:
            excluded_paths = [line.strip() for line in f]

    error_paths = []
    if os.path.isfile('.error_paths'):
        with open('.error_paths', 'r') as f:
            error_paths = [line.strip() for line in f]

    empty_paths = []
    if os.path.isfile('.empty_paths'):
        with open('.empty_paths', 'r') as f:
            empty_paths = [line.strip() for line in f]

    copied_paths = []
    if os.path.isfile('.copied_paths'):
        with open('.copied_paths', 'r') as f:
            copied_paths = [line.strip() for line in f]

    for dirpath, dirnames, filenames in os.walk(source_abspath):
        print(
            'file://{} contains {} directories and {} files'.format(
                    urllib.parse.quote(dirpath), len(dirnames), len(filenames)
                )
        )

        if dirpath in excluded_paths or any(path for path in excluded_paths if dirpath.startswith(path + '/')):
            print('\tpath excluded in a previous run')
            continue

        if not dirnames and not filenames:
            print('\tpath is empty')
            continue

        if dirpath in included_paths:
            print('\tpath included in a previous run')
        else:
            user_input = input('include {}? [y/N]: '.format(dirpath))
            if user_input.lower() == 'y':
                with open('.included_paths', 'a') as f:
                    f.write(dirpath + '\n')
                included_paths.append(dirpath)
                print('\tpath included')
            else:
                with open('.excluded_paths', 'a') as f:
                    f.write(dirpath + '\n')
                excluded_paths.append(dirpath)
                print('\tpath excluded')
                continue

        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            print('\tfile://{}'.format(urllib.parse.quote(file_path)))

            if file_path in error_paths:
                print('\t\tfile had an error in a previous run')
                continue
            if file_path in empty_paths:
                print('\t\tfile was found empty in a previous run')
                continue
            if file_path in copied_paths:
                print('\t\tfile was copied in a previous run')
                continue

            size = None
            try:
                size = os.path.getsize(file_path)
            except OSError as e:
                with open('.error_paths', 'a') as f:
                    f.write(file_path + '\n')
                error_paths.append(file_path)
                print('\t\t{}'.format(e))
                continue

            if size:
                try:
                    cmd = shlex.split('xdg-mime query filetype "{}"'.format(file_path))
                except ValueError as e:
                    with open('.error_paths', 'a') as f:
                        f.write(file_path + '\n')
                    error_paths.append(file_path)
                    print('\t\t{}'.format(e))
                    continue

                with subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    universal_newlines=True
                ) as cmd:
                    mimetype = cmd.stdout.read().strip()
                if not mimetype:
                    print('\t\tmimetype not detected')
                    continue

                if mimetype in excluded_mimetypes:
                    print('\t\tfile has excluded mimetype {}'.format(mimetype))
                    continue
                elif mimetype not in included_mimetypes:
                    user_input = input('\t\tinclude mimetype {}? [y/N]: '.format(mimetype))
                    if user_input.lower() == 'y':
                        with open('.included_mimetypes', 'a') as f:
                            f.write(mimetype + '\n')
                        included_mimetypes.append(mimetype)
                        print('\t\tmimetype included')
                    else:
                        with open('.excluded_mimetypes', 'a') as f:
                            f.write(mimetype + '\n')
                        excluded_mimetypes.append(mimetype)
                        print('\t\tmimetype excluded')
                        continue

                if mimetype.startswith('image'):
                    image_type = imghdr.what(file_path)
                    if not image_type:
                        with open('.error_paths', 'a') as f:
                            f.write(file_path + '\n')
                        error_paths.append(file_path)
                        print('\t\tcould not determine imagetype')
                        continue

                destination_path = os.path.join(destination_abspath, os.path.relpath(file_path, source_abspath))
                extensions = mimetypes.guess_all_extensions(mimetype)
                if extensions and '.' + destination_path.split('.')[-1] not in extensions:
                    destination_path += extensions[0]

                destination_dirname = os.path.dirname(destination_path)
                if not os.path.isdir(destination_dirname):
                    pathlib.Path(destination_dirname).mkdir(parents=True)
                shutil.copy(file_path, destination_path)
                with open('.copied_paths', 'a') as f:
                    f.write(file_path + '\n')
                copied_paths.append(file_path)
                print('\t\tfile copied to {}'.format(destination_path))
            else:
                with open('.empty_paths', 'a') as f:
                    f.write(file_path + '\n')
                empty_paths.append(file_path)
                print('\t\tfile is empty')


if __name__ == '__main__':
    main()
