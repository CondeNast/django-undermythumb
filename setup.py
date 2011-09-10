import os
from setuptools import setup, find_packages


f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = f.read()
f.close()


setup(
    name='django-undermythumb',
    version='0.2.2',
    description="""
The Django thumbnail generation package with a heart of stone.
    """.strip(),
    long_description=readme,
    author='Pitchfork Media, Inc.',
    author_email='dev@pitchfork.com',
    url='http://github.com/pitchfork/django-undermythumb/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
