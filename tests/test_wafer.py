from pytest import mark as m

from npgmlwarehouse.db.wafer import get_records_by_wafer_lims_id


@m.describe("Test data retrieval for a wafer")
class TestProduct(object):
    @m.context("Wafer records are present in `useq_wafer` table")
    @m.it("Retrieves correct records")
    def test_get_wafer_records(self, testdb):
        records = get_records_by_wafer_lims_id(testdb, "122_NT109338I_1")
        assert len(records) == 2
        assert records[0].id_wafer_lims == "122_NT109338I_1"
        assert records[1].id_wafer_lims == "122_NT109338I_1"

        metadata = [
            (w.sample.uuid_sample_lims, w.id_library_lims, w.study.id_study_lims)
            for w in records
        ]
        for md in [
            ("1788c8d0-6a6c-11e4-8e19-68b59977951c", "SQPU-346269-E:A1", "619"),
            ("178df8f0-6a6c-11e4-8e19-68b59977951c", "SQPU-346269-E:A2", "619"),
        ]:
            assert md in metadata

        records = get_records_by_wafer_lims_id(testdb, "123_NT109345H_1")
        assert len(records) == 1
        assert records[0].id_wafer_lims == "123_NT109345H_1"
        assert (
            records[0].sample.uuid_sample_lims == "d41d4a40-a521-11e3-8055-3c4a9275d6c6"
        )

    @m.context("No records for a given ID in `useq_wafer` table")
    @m.it("Returns an empty list")
    def test_get_wafer_records_no_record(self, testdb):
        records = get_records_by_wafer_lims_id(testdb, "122_NT109338I_2")
        assert len(records) == 0
