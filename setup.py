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
        'matplotlib==3.9.3',
        'numpy==2.1.3',
        'requests==2.32.3',
        'scipy==1.14.1',
        'seaborn==0.13.2',
        'setuptools==75.6.0',
    ],
)