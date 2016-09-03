import os
import re
import codecs

from setuptools import setup, find_packages
from setuptools.command.install import install

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def install_completion_script():
    import os
    has_bash = False
    for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, 'bash')
            if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
                has_bash = True

    if not has_bash:
        if os.system('complete') != 0:
            print('\033[93mWarning: you do not have "complete" command, '
                  'the completion feature won\'t be installed.\033[0m')
        else:
            print('\033[93mWarning: "bash" not found, the completion feature won\'t be installed.\033[0m')
        return

    if not os.path.isdir('/etc'):
        print('\033[93mWarning: you do not have an unix environment, I cannot install the completion script.'
              'Please install it manually by copying ovhcli_complete.sh to the correct folder '
              'so it is executed at startup.\033[0m')
        return

    if not os.path.isdir('/etc/bash_completion.d'):
        print('\033[93mWarning: you do not have a "/etc/bash_completion.d" folder, the completion script will not '
              'be installed. If you want to activate it, source ovhcli_complete.sh.\033[0m')
        return

    with open('/etc/bash_completion.d/ovhcli', 'w+') as f:
        f.write(read('ovhcli_complete.sh'))

    try:
        os.chmod('/etc/bash_completion.d/ovhcli', 0o644)
    except OSError:
        pass
    print('\033[94mOVH CLI completion script installed at "/etc/bash_completion.d/ovhcli".\n'
          'You will need to reload your shell or source it to activate the script.\033[0m')


class PostInstallCommand(install):
    def run(self):
        install_completion_script()
        install.run(self)

setup(
    name="ovh_api_cli",
    version=find_version("ovh_api_cli", "__init__.py"),
    description="A wrapper over OVH's API with killer autocomplete feature.",
    long_description=read('README.rst'),
    classifiers=[
        "Topic :: Utilities",
        "Environment :: Console",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    keywords='ovh cli api apiv6',
    author='Cyril DEMINGEON',
    author_email='cyril.demingeon@corp.ovh.com',
    url='https://api.ovh.com/',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'data': ['README.md', 'ovhcli_complete.sh', '*.py']
    },
    entry_points={
        "console_scripts": [
            "ovhcli=ovh_api_cli:main"
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    }
)
