import json

import pytest

import npgmlwarehouse.db.schema
from npgmlwarehouse.db.utils import MlwarehouseConfig, insert_from_yaml, test_db_session


@pytest.fixture(scope="function")
def testdb():
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
    with test_db_session(mlwh_config, npgmlwarehouse.db.schema.Base) as session:
        insert_from_yaml(session, "tests/data/db_fixtures", "npgmlwarehouse.db.schema")
        yield session
