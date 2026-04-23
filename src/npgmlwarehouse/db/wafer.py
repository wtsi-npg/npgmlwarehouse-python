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

"""
Functions for retrieving the barcoded moieties loaded into one wafer.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from npgmlwarehouse.db.schema import (
    Sample,
    Study,
    UseqWafer,
)


def get_records_by_wafer_lims_id(
    session: Session, id_wafer_lims: str
) -> Sequence[UseqWafer]:
    """
    Get all LIMS entities that correspond to an Ultimagen wafer along with
    their sample and study data.

    Args:
        session (sqlalchemy.orm.Session):
            Database session
        id_wafer_lims (str): Unique ID for an Ultimagen wafer which consists of
            <batch_for_opentrons>_<pool_barcode>_<count>. The count is used to
            disambiguate multiple wafers which were processed in the same batch
            opentrons process for the same library pool.

    Returns:
        Sequence[UseqWafer]: Collection of wafer records
    """
    query = (select(UseqWafer).join(Sample).join(Study)).where(
        UseqWafer.id_wafer_lims == id_wafer_lims
    )
    return session.scalars(query).all()
