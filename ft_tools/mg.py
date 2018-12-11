from __future__ import print_function
import re
from launchpadlib.launchpad import Launchpad

from ft_tools.utils import info, info2

LP_CACHEDIR = '.launchpadlib/cache'
MG5 = None
VERSIONS = {}


def _login():
    global MG5
    if MG5 is None:
        lp = Launchpad.login_anonymously('just testing', 'production', LP_CACHEDIR, version='devel')
        MG5 = lp.projects['mg5amcnlo']


def get_versions():
    if VERSIONS:
        return VERSIONS
    _login()
    for release in MG5.releases:
        for file in release.files:
            fname = file.self_link.split('/')[-1]
            # print(fname)
            v_maj, v_min, v_bfx, _, v_ext = re.findall(r'.*v([0-9]+)[\._]([0-9]+)[\._]([0-9]+)([\._](.*))?.tar.gz', fname)[0]
            v_name = '_'.join([v_maj, v_min, v_bfx])
            if v_ext:
                v_name += '_' + v_ext
            VERSIONS[v_name] = file
    return VERSIONS


def check_install(version_name):
    from os.path import isdir
    if isdir(version_name):
        return True, version_name
    elif isdir('MG5_aMC_v'+version_name):
        return True, 'MG5_aMC_v'+version_name
    else:
        return False, 'MG5_aMC_v'+version_name


def replace_in_file(fname, from_, to):
    with open(fname, 'r') as f:
        orig_txt = f.read()
    edited_txt = orig_txt.replace(from_, to)
    with open(fname, 'w') as f:
        f.write(edited_txt)


def install_version(version_name):
    from shutil import move
    from os import makedirs, remove, removedirs
    from os.path import isdir
    from glob import glob
    import tarfile

    dest = 'MG5_aMC_v'+version_name
    if isdir(dest):
        return
    tmp_tar = 'MG_tmp.tar.gz'
    tmp_dir = 'tmp'
    info('Downloading MG {}'.format(version_name))
    with open(tmp_tar, 'wb') as f:
        raw = get_versions()[version_name].file.open().read()
        f.write(raw)
    info('Unpacking...')
    makedirs(tmp_dir)
    with tarfile.open(tmp_tar, 'r:gz') as f:
        f.extractall(tmp_dir)
    real_dir = glob(tmp_dir+'/*')[0]
    move(real_dir, dest)
    remove(tmp_tar)
    removedirs(tmp_dir)

    info('Installing Models')
    for i, model in enumerate(glob('models/*.tar.gz')):
        info2('{})  {}'.format(i, model))
        with tarfile.open(model, 'r:gz') as f:
            f.extractall(dest + '/models/')

    # Consider tweaks to stop browser opening, make work with gfortran 8+, etc
    # sh('sed', ['-e', 's/# automatic_html_opening = .*/automatic_html_opening = False/', '-i', 'MG5_aMC/input/mg5_configuration.txt'])

    info('Customizing install')
    # MG crashes with gfortran version 8+, enable legacy mode to avoid this
    replace_in_file(dest+'/Template/LO/SubProcesses/makefile',
                    'FFLAGS+= -w', 'FFLAGS+= -w -std=legacy')
    # Tweak config so browser doesn't automatically open upon 'launch'
    replace_in_file(dest+'/input/mg5_configuration.txt',
                    '# automatic_html_opening = True', 'automatic_html_opening = False')
    info('MG ' + version_name + 'installed in ' + dest)


if __name__ == '__main__':
    # for i, v in enumerate(sorted(get_versions())):
    #     print('{}) {}'.format(i, v))
    install_version('2_6_4')
