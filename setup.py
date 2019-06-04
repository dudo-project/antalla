from setuptools import setup, find_packages

setup(
    name="market_data",
    packages=find_packages(), 
    install_requires=[
        "SQLAlchemy",
        "websockets",
    ],
    scripts=["./bin/antalla"],
    package_data={
        "market_data": ["fixtures/coins.json"]
    }
)

    