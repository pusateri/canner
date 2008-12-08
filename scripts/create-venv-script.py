import os

here = os.path.dirname(os.path.abspath(__file__))
script_name = os.path.join(here, 'canner-boot.py')

import virtualenv


EXTRA_TEXT = """
import os, subprocess

CANNER_WRAPPER = '''\
#!/bin/sh
PATH="%(venv)s/bin:$PATH"; export PATH
exec "%(venv)s/bin/canner" "$@"
'''

def after_install(options, home_dir):
    etc = join(home_dir, 'etc')
    if not os.path.exists(etc):
        os.makedirs(etc)

    bin_dir = os.path.abspath(join(home_dir, 'bin'))
    canner_dir = os.path.abspath(join(home_dir, 'canner'))

    subprocess.call([join(bin_dir, 'easy_install'), 'Mercurial'])

    if not os.path.exists(canner_dir):
        subprocess.call(['hg', 'clone', 'http://canner.bangj.com/hg/canner',
                         canner_dir])
    else:
        subprocess.call(['hg', '-R', canner_dir, 'pull', '-u', 
                         'http://canner.bangj.com/hg/canner'])

    subprocess.call([join(bin_dir, 'python'), 'setup.py', 'develop'],
                    cwd=join(home_dir, 'canner'))

    canner_wrapper = join(bin_dir, "canner-wrapper")
    writefile(canner_wrapper,
              CANNER_WRAPPER % {"venv": os.path.abspath(home_dir)})
    make_exe(canner_wrapper)
"""

def main():
    text = virtualenv.create_bootstrap_script(EXTRA_TEXT, python_version='2.5')
    if os.path.exists(script_name):
        f = open(script_name)
        cur_text = f.read()
        f.close()
    else:
        cur_text = ''
    print 'Updating %s' % script_name
    if cur_text == 'text':
        print 'No update'
    else:
        print 'Script changed; updating...'
        f = open(script_name, 'w')
        f.write(text)
        f.close()

if __name__ == '__main__':
    main()

