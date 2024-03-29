from setuptools import setup, find_packages

setup(
    name="antalla",
    packages=find_packages(),
    install_requires=[
        "SQLAlchemy==1.3.2",
        "websockets==9.1",
        "python-dateutil==2.8.0",
        "psycopg2==2.8.1",
        "aiohttp==3.5.4",
        "beautifulsoup4==4.7.1",
        "numpy==1.21.2",
        "seaborn==0.9.0",
        "alembic==1.2.0",
    ],
    extras_require={
        "plots": ["pandas==1.3.2"],
        "dev": [
            "Sphinx==2.2.1",
            "sphinx-rtd-theme==0.4.3",
            "nose",
        ],
    },
    zip_safe=False,
    scripts=["./bin/antalla"],
    package_data={
        "antalla": [
            "fixtures/coins.json",
            "fixtures/exchanges.json",
            "fixtures/coinmarketcap-mappings.json",
            "migrations/alembic.ini",
        ]
    },
)
