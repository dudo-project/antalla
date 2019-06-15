from setuptools import setup, find_packages

setup(
    name="antalla",
    packages=find_packages(), 
    install_requires=[
        "SQLAlchemy",
        "websockets",
        "python-dateutil",
        "psycopg2",
        "aiohttp"
    ],
    scripts=["./bin/antalla"],
    package_data={
        "antalla": [
            "fixtures/coins.json",
            "fixtures/exchanges.json",
        ]
    }
)

