from setuptools import setup

setup(
    name="pgindexrebuild",
    version="0.17.0rc1",
    author="Amanda McCann",
    author_email="amanda@geofabrik.de",
    py_modules=['pgindexrebuild'],
    platforms=['any',],
    license = 'GPLv3+',
    url = 'https://github.com/amandasaurus/pgindexrebuild',
    install_requires=[
        'psycopg2',
        "humanfriendly",
        ],
    entry_points={
        'console_scripts': [
            'pgindexrebuild = pgindexrebuild:main',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Operating System :: Unix',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: System :: Systems Administration',
        'Programming Language :: Python :: 3',
    ],
)
