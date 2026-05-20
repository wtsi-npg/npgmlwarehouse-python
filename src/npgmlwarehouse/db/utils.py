# -*- coding: utf-8 -*-
#
# Copyright © 2026 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Generator

import yaml
from sqlalchemy import create_engine, engine, insert
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy_utils import create_database, database_exists, drop_database


@dataclass
class MlwarehouseConfig:
    dbhost: str
    dbport: str
    dbuser: str
    dbname: str
    dbpass: str = field(repr=False)

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


def db_session(config: MlwarehouseConfig) -> Generator[Session, Any, None]:
    engine = create_engine(config.url)
    with Session(engine) as session:
        yield session


@contextmanager
def test_db_session(
    config: MlwarehouseConfig, schema_base: type[DeclarativeBase]
) -> Generator[Session, Any, None]:
    engine = create_engine(config.url)
    try:
        if not database_exists(engine.url):
            create_database(engine.url)
        schema_base.metadata.create_all(engine)

        with Session(engine) as session:
            yield session
    finally:
        drop_database(engine.url)
