from setuptools import setup, find_packages

setup(
    name="antalla",
    packages=find_packages(), 
    install_requires=[
    "SQLAlchemy==1.3.2",
    "websockets==7.0",
    "python-dateutil==2.8.0",
    "psycopg2==2.8.1",
    "aiohttp==3.5.4",
    "beautifulsoup4==4.7.1"
    ],
    scripts=["./bin/antalla"],
    package_data={
        "antalla": [
            "fixtures/coins.json",
            "fixtures/exchanges.json",
        ]
    }
)

