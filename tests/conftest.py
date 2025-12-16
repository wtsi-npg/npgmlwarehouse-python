import json
import os
import re
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine, engine, insert
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from npgmlwarehouse.db.schema import Base


@dataclass
class MlwarehouseConfig:
    dbhost: str
    dbport: str
    dbuser: str
    dbname: str
    dbpass: str

    @property
    def url(self):
        return engine.URL(
            "mysql+pymysql",
            self.dbuser,
            self.dbpass,
            self.dbhost,
            int(self.dbport),
            self.dbname,
            {"charset": "utf8mb4"},
        )


def insert_from_yaml(session: Session, dir_path: str | Path, schema_path: str):
    """
    Load the schema module where the ORM table classes are defined.

    Args:
        session (sqlalchemy.orm.Session): DB connection class which uses create_engine() object
        dir_path (str | Path): Path of yml modules
        schema_path (str): File with the schema module of the database
    """
    schema_module = import_module(schema_path)

    dir_obj = Path(dir_path)
    file_paths = list(str(f) for f in dir_obj.iterdir())
    file_paths.sort()

    for file_path in file_paths:
        with open(file_path, "r") as f:
            (_, file_name) = os.path.split(file_path)
            m = re.match(r"\A\d+-([a-zA-Z]+)\.yml\Z", file_name)
            if m is not None:
                class_name = m.group(1)
                table_class = getattr(schema_module, class_name)
                data = yaml.safe_load(f)
                session.execute(insert(table_class), data)

    session.commit()


@pytest.fixture(scope="module")
def mlwh_session():
    """
    A fixture that populates a MySQL database
    with pre-defined fixtures.
    """
    with open("tests/config/testdb.json", "r") as json_input:
        config = json.loads(json_input.read())["MLWH"]
        mlwh_config = MlwarehouseConfig(
            dbhost=config["dbhost"],
            dbport=config["dbport"],
            dbuser=config["dbuser"],
            dbname=config["dbname"],
            dbpass=config["dbpass"],
        )
    engine = create_engine(mlwh_config.url)
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        try:
            insert_from_yaml(
                session, "tests/data/db_fixtures", "npgmlwarehouse.db.schema"
            )
            yield session
        finally:
            session.close()
            drop_database(engine.url)
