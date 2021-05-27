"""simple set up"""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_install_requires():
    install_requires = [
        'termcolor',
        'tabulate',
    ]
    return install_requires

def get_version():
    version_file = "minisocket/version.py"
    with open(version_file, 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']

if __name__ == "__main__":
    setuptools.setup(
        name="minisocket", 
        version=get_version(),
        author="Liuchun Yuan",
        author_email="ylc0003@gmail.com",
        description="socket api",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/LicharYuan/mini-socket",
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",


        ],
        python_requires='>=3.5',
        install_requires = get_install_requires(),
    )

