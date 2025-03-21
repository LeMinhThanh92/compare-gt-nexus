import sqlalchemy
from sqlalchemy import text

def get_db_engine():

    connection_url = sqlalchemy.engine.URL.create(
        "mssql+pyodbc",
        query={
            "odbc_connect": (
                "DRIVER=SQL Server;"
                "SERVER=localhost;"
                "DATABASE=HR;"
                "UID=sa;"
                "PWD=123;"
                "TrustServerCertificate=yes;"
            )
        }
    )
    return sqlalchemy.create_engine(connection_url)


def run_query(engine, query, params=None):

    params = params or {}
    with engine.begin() as connection:
        result = connection.execute(query, params)
        return result.rowcount


def import_json_to_db(table):

    engine = get_db_engine()

    json_data = table.to_json(orient='records', date_format='iso', indent=4)
    query_string = text("EXEC [dbo].[Import_Json] @json = :json")

    row_count = run_query(engine, query_string, {"json": json_data})

    return True if row_count > 0 else False

