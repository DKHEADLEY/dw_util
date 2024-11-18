from setuptools import setup, find_packages

setup(
    name='dwave-domain-wall',
    version='0.1.0',
    description='D-Wave package for encoding problems in domain wall variables',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'dwave-ocean-sdk',
        # Add other dependencies here
    ],
)