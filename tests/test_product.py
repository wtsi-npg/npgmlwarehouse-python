from pytest import mark as m
from sqlalchemy import select

from npgmlwarehouse.db.product import (
    create_upload_irods_location_records,
    get_ultimagen_target_product_records,
)
from npgmlwarehouse.db.schema import SeqProductIrodsLocations


@m.describe("TestProduct")
class TestProduct(object):
    @m.context("When product records are present in `useq_product_metrics` table")
    @m.it("Retrieves the product record rows from MLWH")
    def test_get_product_records(self, mlwh_session):
        records = get_ultimagen_target_product_records(mlwh_session, 51579)
        assert len(records) == 4

    @m.context("When there is no product records in `useq_product_metrics` table")
    @m.it("Returns an empty collection")
    def test_get_product_records_no_record(self, mlwh_session):
        records = get_ultimagen_target_product_records(mlwh_session, 40000)
        assert len(records) == 0

    @m.context("When a location record is added to `seq_product_irods_locations`")
    @m.it("Location record is present and correct")
    def test_create_upload_irods_location_records(self, mlwh_session):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        id_product = "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        coll = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        prod_coll = {id_product: coll}
        create_upload_irods_location_records(
            mlwh_session, prod_coll, platform, pipeline
        )

        record = mlwh_session.scalars(
            select(SeqProductIrodsLocations).where(
                SeqProductIrodsLocations.id_product == id_product,
            )
        ).first()
        assert record.id_product == id_product
        assert record.seq_platform_name == platform
        assert record.pipeline_name == pipeline
        assert record.irods_root_collection == coll

    @m.context("When multiple locations are added to `seq_product_irods_locations`")
    @m.it("Location records are present")
    def test_create_upload_irods_location_records_multiple(self, mlwh_session):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        prod_coll = {
            "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32": "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT",
            "4710c1002d44c4dee326f91a663e223e6e8f64fe866ab84b7a5f264ae0028396": "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s2-Z0002-CATGTGCAGCCATCGAT",
        }
        create_upload_irods_location_records(
            mlwh_session, prod_coll, platform, pipeline
        )

        records = mlwh_session.scalars(
            select(SeqProductIrodsLocations).where(
                SeqProductIrodsLocations.seq_platform_name == platform,
            )
        ).all()
        assert len(records) == 2
