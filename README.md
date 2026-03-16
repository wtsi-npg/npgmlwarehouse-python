# npgmlwarehouse-python
ORM and access layer for the existing MySQL multi-lims warehouse

This package contains an ORM for an existing multi-lims warehouse database schema, 
which hosts information about runs, samples and studies. A Perl ORM for the same schema 
is defined in [ml_warehouse](https://github.com/wtsi-npg/ml_warehouse).
Migrations for that schema are also tracked in the Perl package.

The code in this package was tested for read and write operations. Most of the business
logic for `create` and `update` operation for different database tables is implemented
in the Perl package. We advise against performing `write` operations using this ORM.

Currently, record creation from this code is performed only on the iRODS location table
`seq_product_irods_locations`. We allow for vendor-specific `sqlalchemy` code where trying
to be vendor-agnostic would result in implementing a large volume of custom code and tests.

This ORM has been auto-generated with [`sqlacodegen 3.1.1`](https://pypi.org/project/sqlacodegen/3.1.1/) 

```
sqlacodegen --generator declarative mysql+pymysql://user:pass@host:port/dbname > src/npgmlwarehouse/db/schema.py
```

## Development

The project follows Google code and documentation [style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).
Linting should be performed by `ruff`.

Unit tests are performed against an instance of MySQL server.

Installation and testing:

```
pip install .[test]
pytest
```
