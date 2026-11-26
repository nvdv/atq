"""Setup script for atq."""
from setuptools import setup


def get_description():
    """Reads README.md file."""
    with open('README.md', encoding='utf-8') as readme_file:
        return readme_file.read()


setup(
    name='atq',
    version='0.0.2',
    packages=['atq'],
    description='Async task queue for Python',
    long_description=get_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/nvdv/atq',
    license='BSD',
    author='nvdv',
    author_email='aflatnine@gmail.com',
    keywords=['task queue', 'asyncio', 'async'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Software Development',
    ],
    entry_points={
        'console_scripts': [
            'atqserver = atq.__main__:main'
        ]
    },
    install_requires=[
        'cloudpickle>=3.0.0',
    ],
    python_requires='>=3.9',
)
