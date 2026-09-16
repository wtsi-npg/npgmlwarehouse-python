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

from sqlalchemy import or_, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from npgmlwarehouse.db.schema import (
    Sample,
    SeqProductIrodsLocations,
    Study,
    UseqProductMetrics,
)


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


def validate_studies(session: Session, study_ids: list[str]):
    """
    Validates a list of string study IDs.

    Validates a list of study IDs by checking whether the `study` table
    record is available for each of the IDs. The input least can contain
    duplicate values. An empty input list will cause an error.

    Errors if any of the given study IDs
      * is not a string,
      * is invalid, the error message lists all invalid IDs,
      * maps to multiple database rows.

    Args:
        session (Session):
            Database session.
        study_ids (str):
            Study IDs to validate.
    Returns:
        True if all sudies have been validated.
    """

    if len(study_ids) == 0:
        raise ValueError("A non-empty list of string study IDs is required")
    if len([id for id in study_ids if isinstance(id, str)]) < len(study_ids):
        raise TypeError("All study IDs should be strings")

    unique_ids = set(study_ids)

    q = select(Study.id_study_lims).where(Study.id_study_lims.in_(unique_ids))
    available = session.scalars(q).all()
    missing = [study_id for study_id in unique_ids if study_id not in available]
    if len(missing):
        raise ValueError(
            "Invalid stud{end}: {list_of}".format(
                end="y" if len(missing) == 1 else "ies",
                list_of=", ".join(sorted(missing)),
            )
        )
    if len(available) > len(unique_ids):
        raise Exception(
            (
                "Duplicate MLWH rows for some IDs in "
                f"{', '.join(sorted(list(unique_ids)))}"
            )
        )

    return True


def get_sample_id_for_name(session: Session, sample_name: str) -> str | None:
    """
    Retrieves sample ID for the sample name given as the argument.

    Searches the `sample` table for a record with the given name. Examines
    values in two columns - `name` and `supplier_name`.

    Errors if multiple records are found. Returns sample's ID if a single
    record is found or `None` if no record is found.

    Args:
        session (Session):
            Database session.
        name (name):
            Sample name.
    Returns:
        String sample ID if found or None
    """
    if not isinstance(sample_name, str):
        raise TypeError("sample_name argument should be a string")
    if not sample_name:
        raise ValueError("sample_name argument should be a non-empty string")

    q = select(Sample.id_sample_lims).where(
        or_(Sample.name == sample_name, Sample.supplier_name == sample_name)
    )
    return session.scalars(q).one_or_none()


def create_upload_irods_location_records(
    session: Session,
    product_data: dict[str, dict],
    seq_platform_name: str,
    pipeline_name: str,
):
    """
    Insert product records identified by their product IDs into the iRODS location
    table `seq_product_irods_locations`. In the case a record with this `id_product` and
    `irods_root_collection` exists in the database no error will be raised.
    Records are updated accordingly.

    `product_data` should have the following structure where the last two keys are
    optional. When not specified, the update to NULL will be issued:

        product_data[`id_product`] = {
            "irods_root_collection": "/irods/path/to/collection1",
            "irods_data_relative_path": "/irods/path/to/data1",
            "irods_secondary_data_relative_path": "/irods/path/to/secondary/data1",
        }

    Args:
        session (Session):
            Database connection Session
        product_data (dict[str, dict]):
            Dictionary composed in the following way:
            key: sequencing product ID (str)
            value: Dictionary of Column (str), iRODS path (str).
            Column names:
                `irods_root_collection`, `irods_data_relative_path`, `irods_secondary_data_relative_path`
        seq_platform_name (str):
            Platform name common to all records
        pipeline_name (str):
            Pipeline name common to all records

    Returns:
        None
    """
    if not product_data:
        return

    to_insert = []
    for id_product, data in product_data.items():
        data_to_insert = {
            "id_product": id_product,
            "seq_platform_name": seq_platform_name,
            "pipeline_name": pipeline_name,
            "irods_root_collection": data["irods_root_collection"],
            "irods_data_relative_path": data.get("irods_data_relative_path", None),
            "irods_secondary_data_relative_path": data.get(
                "irods_secondary_data_relative_path", None
            ),
        }
        to_insert.append(data_to_insert)

    insert_query = insert(SeqProductIrodsLocations).values(to_insert)
    on_duplicate_kwargs = {
        "seq_platform_name": insert_query.inserted.seq_platform_name,
        "pipeline_name": insert_query.inserted.pipeline_name,
        "irods_data_relative_path": insert_query.inserted.irods_data_relative_path,
        "irods_secondary_data_relative_path": insert_query.inserted.irods_secondary_data_relative_path,
    }

    insert_on_duplicate = insert_query.on_duplicate_key_update(**on_duplicate_kwargs)
    session.execute(insert_on_duplicate)
    session.commit()
