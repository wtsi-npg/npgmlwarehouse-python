# npgmlwarehouse-python
ORM and access layer for the existing multi-lims warehouse

This package contains an ORM for an existing multi-lims warehouse database schema, 
which hosts information about runs, samples and studies. A Perl ORM for the same schema 
is defined in [ml_warehouse](https://github.com/wtsi-npg/ml_warehouse).
Migrations for that schema are also tracked in the Perl package.

The code in this package was tested for read-only operations. Business logic
for `create` and `update` operation for different database tables is implemented
in the Perl package. We advise against performing `write` operations using this ORM.

This ORM has been auto-generated with [`sqlacodegen 3.1.1`](https://pypi.org/project/sqlacodegen/3.1.1/) 

```
sqlacodegen --generator declarative mysql+pymysql://user:pass@host:port/dbname > src/npgmlwarehouse/db/schema.py
```

## Development

The project follows Google code and documentation [style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).
Linting should be performed by `ruff`.

Installation and testing:

```
pip install .[test]
pytest
```
