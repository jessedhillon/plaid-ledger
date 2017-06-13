from setuptools import setup, find_packages


setup(
    name='plaid_ledger',
    version='0.0',
    description="Plaid Ledger",
    author="Jesse Dhillon",
    author_email="jesse@dhillon.com",
    url="http://plaid.com/",
    requires=[
        'click',
        'colorlog',
        'plaid_python',
        'pygments',
        'PyYAML',
    ],
    entry_points={
        'console_scripts': ['pledger=plaid_ledger.commands:main']
    })
