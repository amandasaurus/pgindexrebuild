from setuptools import setup

setup(
    name="pgindexrebuild",
    version="0.7.0",
    author="Rory McCann",
    author_email="rory@geofabrik.de",
    py_modules=['pgindexrebuild'],
    platforms=['any',],
    install_requires=[
        'psycopg2',
        ],
    entry_points={
        'console_scripts': [
            'pgindexrebuild = pgindexrebuild:main',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
    ],
)
