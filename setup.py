from setuptools import setup
setup(
    name='MandarinListeningTrainer',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'mltrain=train:run',
            'mlplot=stats:plot',
        ]
    },
    install_requires=[
        'numpy',
        'pydub',
        'requests',
        'scipy',
        'matplotlib',
        'seaborn'
    ],
)