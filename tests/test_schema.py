from pytest import mark as m
from sqlalchemy.orm import Session

from npgmlwarehouse.db.schema import (
    Sample,
    Study,
    UseqWafer,
)


def get_wafer_data(session: Session, id_wafer_lims: str) -> list[UseqWafer]:
    """
    Get the wafer data for an Ultimagen run with sample and study metadata.

    Args:
        session (sqlalchemy.orm.Session):
            Database session
        id_wafer_lims (str): Unique ID for Ultimagen runs which consists of
            <batch_for_opentrons>_<id_pool_id>_<runcount>

    Returns:
    -------
        list[UseqWafer]: Collection of samples from wafer data
    """
    query = (session.query(UseqWafer).join(Sample).join(Study)).filter(
        UseqWafer.id_wafer_lims == id_wafer_lims
    )
    return query.all()


@m.describe("SchemaModel")
class TestSchemaModel(object):
    @m.context("When retrieving wafer records from mlwarehouse")
    @m.context("When there are no samples associated to it")
    @m.it("Empty list is returned")
    def test_schema_no_sample(self, mlwh_session):
        wafer_data = get_wafer_data(mlwh_session, "100_NT109338I_1")
        assert len(wafer_data) == 0

    @m.context("When retrieving wafer records from mlwarehouse")
    @m.context("When there is one sample in a wafer")
    @m.it("A single sample is returned")
    def test_schema_single_samples(self, mlwh_session):
        wafer_data = get_wafer_data(mlwh_session, "123_NT109345H_1")
        assert len(wafer_data) == 1
        metadata = wafer_data.pop()
        assert (
            "d41d4a40-a521-11e3-8055-3c4a9275d6c6" == metadata.sample.uuid_sample_lims
        )

    @m.context("When retrieving wafer records from mlwarehouse")
    @m.context("When a wafer has multiple samples")
    @m.it("Metadata of the returned samples are correct")
    def test_schema_multiple_samples(self, mlwh_session):
        wafer_data = get_wafer_data(mlwh_session, "122_NT109338I_1")
        assert len(wafer_data) == 2
        metadata = [
            (w.sample.uuid_sample_lims, w.id_library_lims, w.study.id_study_lims)
            for w in wafer_data
        ]
        for md in [
            ("1788c8d0-6a6c-11e4-8e19-68b59977951c", "SQPU-346269-E:A1", "619"),
            ("178df8f0-6a6c-11e4-8e19-68b59977951c", "SQPU-346269-E:A2", "619"),
        ]:
            assert md in metadata
