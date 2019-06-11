from setuptools import setup, find_packages

setup(
    name="antalla",
    packages=find_packages(), 
    install_requires=[
        "SQLAlchemy",
        "websockets",
        "python-dateutil",
    ],
    scripts=["./bin/antalla"],
    package_data={
        "antalla": ["fixtures/coins.json"]
    }
)

    