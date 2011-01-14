import os
from setuptools import setup, find_packages


f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = f.read()
f.close()


setup(
    name='django-undermythumb',
    version='0.1',
    description="""
        django-undermythumb is a reusable Django application
        for easy thumb creation and access.
    """,
    long_description=readme,
    author='Sean Brant',
    author_email='seanb@pitchfork.com',
    url='http://github.com/seanbrant/django-undermythumb/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
