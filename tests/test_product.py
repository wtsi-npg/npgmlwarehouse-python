from time import sleep

from pytest import mark as m
from sqlalchemy import select

from npgmlwarehouse.db.product import (
    create_upload_irods_location_records,
    get_ultimagen_target_product_records,
)
from npgmlwarehouse.db.schema import SeqProductIrodsLocations


def select_locations_byplatform(platform_name: str):
    return select(SeqProductIrodsLocations).where(
        SeqProductIrodsLocations.seq_platform_name == platform_name,
    )


@m.describe("TestProduct")
class TestProduct(object):
    @m.context("When product records are present in `useq_product_metrics` table")
    @m.it("Retrieves the product records from MLWH")
    def test_get_product_records(self, testdb):
        records = get_ultimagen_target_product_records(testdb, 51579)
        assert len(records) == 4

    @m.context("When there is no product records in `useq_product_metrics` table")
    @m.it("Returns an empty collection")
    def test_get_product_records_no_record(self, testdb):
        records = get_ultimagen_target_product_records(testdb, 40000)
        assert len(records) == 0

    @m.context("When inserting a product record in `seq_product_irods_locations`")
    @m.it("Location record is present and correct")
    def test_create_upload_irods_location_records(self, testdb):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        id_product = "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        coll = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        product_data = {
            id_product: {
                "irods_root_collection": coll,
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            }
        }
        create_upload_irods_location_records(testdb, product_data, platform, pipeline)

        record = testdb.scalars(
            select(SeqProductIrodsLocations).where(
                SeqProductIrodsLocations.id_product == id_product,
            )
        ).first()
        assert record.id_product == id_product
        assert record.seq_platform_name == platform
        assert record.pipeline_name == pipeline
        assert record.irods_root_collection == coll

    @m.context("When using an empty collection in create_upload_irods_location")
    @m.it("Function returns early")
    def test_create_upload_irods_location_empty_input(self, testdb):
        platform = "Ultimagen"
        pipeline = "instrument_output"

        create_upload_irods_location_records(testdb, {}, platform, pipeline)

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 0

    @m.context(
        "When inserting multiple product records in `seq_product_irods_locations`"
    )
    @m.it("Location records are present")
    def test_create_upload_irods_location_records_multiple(self, testdb):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        product_data = {
            "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32": {
                "irods_root_collection": "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT",
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            },
            "4710c1002d44c4dee326f91a663e223e6e8f64fe866ab84b7a5f264ae0028396": {
                "irods_root_collection": "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s2-Z0002-CATGTGCAGCCATCGAT",
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            },
        }
        create_upload_irods_location_records(testdb, product_data, platform, pipeline)

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 2

    @m.context("When inserting a product record in `seq_product_irods_locations`")
    @m.context("When the unique key is duplicated")
    @m.context("When the record has the same pipeline and platform names")
    @m.it("Ignores the row update")
    def test_create_upload_irods_location_records_duplicate_unique_key_same_pipeline_platform(
        self, testdb
    ):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        id_product = "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        coll = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        testdb.add(
            SeqProductIrodsLocations(
                id_product=id_product,
                seq_platform_name=platform,
                pipeline_name=pipeline,
                irods_root_collection=coll,
            )
        )
        testdb.commit()
        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1
        last_changed = records.pop().last_changed

        sleep(2)
        product_data = {
            id_product: {
                "irods_root_collection": coll,
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            }
        }
        create_upload_irods_location_records(
            testdb,
            product_data,
            platform,
            pipeline,
        )

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1
        record = records.pop()
        assert record.last_changed == last_changed
        assert record.id_product == id_product
        assert record.irods_root_collection == coll
        assert record.seq_platform_name == platform
        assert record.pipeline_name == pipeline

    @m.context(
        "When inserting multiple product records in `seq_product_irods_locations`"
    )
    @m.context("When one of them has a duplicate unique key")
    @m.context("When the duplicate record has the same values")
    @m.it("Ignores the duplicate record insertion and continues")
    def test_create_upload_irods_location_records_continues_on_duplicate_unique_key(
        self, testdb
    ):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        id_product_dup = (
            "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        )
        coll_dup = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        testdb.add(
            SeqProductIrodsLocations(
                id_product=id_product_dup,
                seq_platform_name=platform,
                pipeline_name=pipeline,
                irods_root_collection=coll_dup,
            )
        )
        testdb.commit()
        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1

        product_data = {
            id_product_dup: {
                "irods_root_collection": coll_dup,
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            },
            "4710c1002d44c4dee326f91a663e223e6e8f64fe866ab84b7a5f264ae0028396": {
                "irods_root_collection": "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s2-Z0002-CATGTGCAGCCATCGAT",
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            },
        }
        create_upload_irods_location_records(testdb, product_data, platform, pipeline)

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 2
        for record in records:
            assert record.id_product in product_data
            assert (
                record.irods_root_collection
                == product_data[record.id_product]["irods_root_collection"]
            )

    @m.context("When inserting a product record in `seq_product_irods_locations`")
    @m.context("When the unique key is duplicated")
    @m.context("When the new pipeline name is different")
    @m.it("Updates the pipeline name")
    def test_create_upload_irods_location_records_update_pipeline(self, testdb):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        newpipeline = "ultimagen_pipeline"
        id_product = "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        coll = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        product_data = {
            id_product: {
                "irods_root_collection": coll,
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            }
        }
        testdb.add(
            SeqProductIrodsLocations(
                id_product=id_product,
                seq_platform_name=platform,
                pipeline_name=pipeline,
                irods_root_collection=coll,
            )
        )
        testdb.commit()
        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1

        create_upload_irods_location_records(
            testdb,
            product_data,
            platform,
            newpipeline,
        )

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1
        record = records.pop()
        assert record.id_product == id_product
        assert record.irods_root_collection == coll
        assert record.pipeline_name == newpipeline

    @m.context("When inserting a product record in `seq_product_irods_locations`")
    @m.context("When the unique key is duplicated")
    @m.context("When the `irods_data_relative_path` is the same")
    @m.context("When the `irods_secondary_data_relative_path` is the same")
    @m.it("Does not issue the update to the record")
    def test_create_upload_irods_location_records_duplicate_unique_key_full_input_no_update(
        self, testdb
    ):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        id_product = "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        coll = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        data_relative_path = (
            "434523-1-Z0025-CTCGAGATTGATGAT_S1_L001_R2_001_sample.fastq.gz"
        )
        secondary_data_relative_path = "434523-1-Z0025-CTCGAGATTGATGAT.csv"
        testdb.add(
            SeqProductIrodsLocations(
                id_product=id_product,
                seq_platform_name=platform,
                pipeline_name=pipeline,
                irods_root_collection=coll,
                irods_data_relative_path=data_relative_path,
                irods_secondary_data_relative_path=secondary_data_relative_path,
            )
        )
        testdb.commit()
        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1
        last_changed = records.pop().last_changed

        sleep(2)
        product_data = {
            id_product: {
                "irods_root_collection": coll,
                "irods_data_relative_path": data_relative_path,
                "irods_secondary_data_relative_path": secondary_data_relative_path,
            }
        }
        create_upload_irods_location_records(
            testdb,
            product_data,
            platform,
            pipeline,
        )

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1
        record = records.pop()
        assert record.last_changed == last_changed
        assert record.irods_data_relative_path == data_relative_path
        assert record.irods_secondary_data_relative_path == secondary_data_relative_path

    @m.context("When inserting a product record in `seq_product_irods_locations`")
    @m.context("When the unique key is duplicated")
    @m.context("When the `irods_data_relative_path` is to be updated with NULL")
    @m.context(
        "When the `irods_secondary_data_relative_path` is to be updated with NULL"
    )
    @m.it("Inserts NULL in the mentioned columns")
    def test_create_upload_irods_location_records_duplicate_unique_key_full_input_update(
        self, testdb
    ):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        id_product = "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        coll = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        data_relative_path = (
            "434523-1-Z0025-CTCGAGATTGATGAT_S1_L001_R2_001_sample.fastq.gz"
        )
        secondary_data_relative_path = "434523-1-Z0025-CTCGAGATTGATGAT.csv"
        testdb.add(
            SeqProductIrodsLocations(
                id_product=id_product,
                seq_platform_name=platform,
                pipeline_name=pipeline,
                irods_root_collection=coll,
                irods_data_relative_path=data_relative_path,
                irods_secondary_data_relative_path=secondary_data_relative_path,
            )
        )
        testdb.commit()
        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1

        product_data = {
            id_product: {
                "irods_root_collection": coll,
                "irods_data_relative_path": None,
                "irods_secondary_data_relative_path": None,
            }
        }
        create_upload_irods_location_records(
            testdb,
            product_data,
            platform,
            pipeline,
        )

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1
        record = records.pop()
        assert record.irods_data_relative_path == None
        assert record.irods_secondary_data_relative_path == None

    @m.context("When inserting a product record in `seq_product_irods_locations`")
    @m.context("When the unique key is duplicated")
    @m.context(
        "When the input for `irods_data_relative_path` and `irods_secondary_data_relative_path` is not specified"
    )
    @m.it("Updates the mentioned columns to NULL by default")
    def test_create_upload_irods_location_records_duplicate_unique_key_part_input_update(
        self, testdb
    ):
        platform = "Ultimagen"
        pipeline = "instrument_output"
        id_product = "244c6fce98d0261f25cedd81dbfcfc08e2207c954c8e25f471f5b6aaca144a32"
        coll = "/testZone/home/irods/ultimagen/434895-20260110_0323/434895-s1-Z0001-CAGCTCGAATGCGAT"
        data_relative_path = (
            "434523-1-Z0025-CTCGAGATTGATGAT_S1_L001_R2_001_sample.fastq.gz"
        )
        secondary_data_relative_path = "434523-1-Z0025-CTCGAGATTGATGAT.csv"
        testdb.add(
            SeqProductIrodsLocations(
                id_product=id_product,
                seq_platform_name=platform,
                pipeline_name=pipeline,
                irods_root_collection=coll,
                irods_data_relative_path=data_relative_path,
                irods_secondary_data_relative_path=secondary_data_relative_path,
            )
        )
        testdb.commit()
        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1

        product_data = {
            id_product: {
                "irods_root_collection": coll,
            }
        }
        create_upload_irods_location_records(
            testdb,
            product_data,
            platform,
            pipeline,
        )

        records = testdb.scalars(select_locations_byplatform(platform)).all()
        assert len(records) == 1
        record = records.pop()
        assert record.irods_data_relative_path == None
        assert record.irods_secondary_data_relative_path == None
