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

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from npgmlwarehouse.db.schema import SeqProductIrodsLocations, UseqProductMetrics


def get_ultimagen_target_product_records(session: Session, id_run: int):
    """
    Retrieves target Ultimagen product records for a run.

    Args:
        session (Session):
            Database session.
        id_run (int):
            Run ID as saved in tracking DB

    Returns:
        Sequence[UseqProductMetrics]:
            An iterable collection of product records related to the specified run ID.
            An empty Sequence is returned if no product record is found.
    """
    records = session.scalars(
        select(UseqProductMetrics).where(
            UseqProductMetrics.id_run == id_run,
            UseqProductMetrics.is_sequencing_control == 0,
            UseqProductMetrics.tag_index != 0,
        )
    )
    return records.all()


def create_upload_irods_location_records(
    session: Session,
    product_collection: dict[str, str],
    platform_name: str,
    pipeline_name: str,
):
    """
    Insert product records into the iRODS location table
    (`seq_product_irods_locations`) identified by their product IDs.
    In the case of a duplicate entry in the database which corresponds
    to a duplicate unique key of (`id_product`,`irods_root_collection`),
    the insertion is ignored and the function will continue normally
    with no exception.

    Args:
        session (Session):
            Database connection Session
        product_collection (dict[str,str]):
            Dictionary of (sequencing product ID), (iRODS collection path)
        platform_name (str):
            Name of the platform
        pipeline_name (str):
            Name of the pipeline

    Returns:
        None
    """
    if not product_collection:
        return

    to_insert = [
        {
            "id_product": id_product,
            "seq_platform_name": platform_name,
            "pipeline_name": pipeline_name,
            "irods_root_collection": coll,
        }
        for id_product, coll in product_collection.items()
    ]
    session.execute(
        insert(SeqProductIrodsLocations).values(to_insert).prefix_with("IGNORE")
    )
    session.commit()
