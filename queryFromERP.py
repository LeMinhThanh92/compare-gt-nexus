import os
from typing import List

import pandas as pd
import sqlalchemy

from file_utils import read_excel_with_header_detection


def queryFromERP(_file_path: str, folder_path_bulk: str = r'C:\Compare\Bulk'):
    def get_db_engine245():
        """Create database engine for SQL Server connection"""
        connection_url = sqlalchemy.engine.URL.create(
            "mssql+pyodbc",
            query={
                "odbc_connect": (
                    "DRIVER=SQL Server;"
                    "SERVER=192.168.1.245;"
                    "DATABASE=HR;"
                    "UID=user_prog2;"
                    "PWD=qrOZW$v6e1MT;"
                    "TrustServerCertificate=yes;"
                )
            }
        )
        return sqlalchemy.create_engine(connection_url)

    def read_so_and_build_chunks(file_path: str, chunk_size: int = 700) -> tuple[List[str], int]:
        # Read only the SO column once using the shared header detection function
        df = read_excel_with_header_detection(file_path, sheet_name=0, usecols=['SO'])

        so_list = df['SO'].dropna().astype(str).unique()
        so_count = len(so_list)

        formatted_so = [f"('{so}')" for so in so_list]

        # Create chunks
        chunks = []
        for i in range(0, len(formatted_so), chunk_size):
            chunk_values = ",".join(formatted_so[i:i + chunk_size])
            insert_statement = f"INSERT INTO #ItemFilter (SALESID)\nVALUES {chunk_values};"
            chunks.append(insert_statement)

        return chunks, so_count

    def get_temp_table_creation_sql() -> str:
        return "CREATE TABLE #ItemFilter (SALESID NVARCHAR(20));"

    def get_main_query_sql() -> str:
        return """
    SELECT 
        b.SALESID AS 'Sales order',
        b.PURCHORDERFORMNUM AS 'Customer requisition',
        b.CUSTOMERREF AS 'Customer reference',
        b.ITEMID AS 'Item number',
        b.SALESQTY AS 'Quantity',
        b.SALESPRICE AS 'Unit price',
        b.ECCFACTPRICE AS 'Fact price (Unit price)',
        a.TRX_POLAT AS 'PO Line Aggregator',
        a.ECCSALESORDERTYPEID AS 'Sales order type',
        CASE 
            WHEN a.SALESSTATUS = 0 THEN 'Done'
            WHEN a.SALESSTATUS = 1 THEN 'Open order'
            WHEN a.SALESSTATUS = 2 THEN 'Delivered'
            WHEN a.SALESSTATUS = 3 THEN 'Invoiced'
            WHEN a.SALESSTATUS = 4 THEN 'Canceled' 
        END AS 'Status',
        a.ECP2SALESREMARKS AS 'Remark',
        c.INVENTCOLORID AS 'Color',
        c.INVENTSIZEID AS 'Size',
        c.INVENTSTYLEID AS 'Style'
    FROM 
        [192.168.70.115].AxDB.dbo.SALESTABLE AS a
    INNER JOIN 
        [192.168.70.115].AxDB.dbo.SALESLINE AS b
        ON a.SALESID = b.SALESID AND a.DATAAREAID = b.DATAAREAID AND a.PARTITION = b.PARTITION
    INNER JOIN 
        [192.168.70.115].AxDB.dbo.INVENTDIM AS c
        ON b.INVENTDIMID = c.INVENTDIMID AND b.DATAAREAID = c.DATAAREAID AND b.PARTITION = c.PARTITION
    INNER JOIN 
        #ItemFilter AS d ON a.SALESID = d.SALESID
    WHERE 
        a.DATAAREAID = 'a1a'
        AND c.INVENTSTYLEID <> ''
        AND a.PARTITION = 5637144576;
    drop table #ItemFilter    
    """

    def execute_complete_query(insert_chunks: List[str]) -> pd.DataFrame:
        """
        Execute the complete workflow: create temp table, insert data, run main query
        """
        engine = get_db_engine245()

        try:
            with engine.connect() as conn:
                # Start transaction
                trans = conn.begin()

                try:
                    # 1. Create temp table
                    conn.execute(sqlalchemy.text(get_temp_table_creation_sql()))
                    print("✓ Temporary table created")

                    # 2. Insert data in chunks
                    for i, chunk in enumerate(insert_chunks, 1):
                        conn.execute(sqlalchemy.text(chunk))
                        print(f"✓ Chunk {i}/{len(insert_chunks)} inserted")

                    # 3. Execute main query
                    main_query = get_main_query_sql()
                    result = pd.read_sql(main_query, conn)

                    print(f"✓ Query completed. Retrieved {len(result)} rows")

                    # Commit transaction
                    trans.commit()

                    return result

                except Exception as e:
                    trans.rollback()
                    raise e

        except Exception as e:
            print(f"Error: {e}")
            raise

    def preview_chunks(file_path: str, chunks: List[str], chunk_size: int = 700) -> None:
        print(f"File: {file_path}")
        print(f"Total chunks: {len(chunks)}")
        print(f"Chunk size: {chunk_size}")
        print("-" * 50)

        for i, chunk in enumerate(chunks, 1):
            print(f"--- Chunk {i} ---")
            # Show first 200 characters of each chunk
            preview = chunk[:200] + "..." if len(chunk) > 200 else chunk
            print(preview)
            print()

    def export_results(results: pd.DataFrame, folder_path_bulk: str) -> str:
        """
        Export results to Excel file in the specified bulk folder
        """
        try:
            # Create the bulk directory if it doesn't exist
            os.makedirs(folder_path_bulk, exist_ok=True)

            # Create output filename with fixed name 'Order lines'
            output_filename = "Order lines_ERP.xlsx"
            output_path = os.path.join(folder_path_bulk, output_filename)

            # Export to Excel
            results.to_excel(output_path, index=False, engine='openpyxl')

            print(f"✓ Results exported to: {output_path}")
            print(f"✓ Total rows exported: {len(results)}")

            return output_path

        except Exception as e:
            print(f"Error exporting results: {e}")
            raise

    # file_path = r'C:\Compare\testWeekly.xlsx'

    insert_chunks, so_count = read_so_and_build_chunks(_file_path, chunk_size=700)

    print("=== PREVIEW ===")
    preview_chunks(_file_path, insert_chunks)

    print(f"Total unique SO values: {so_count}")

    print("\n=== EXECUTING QUERY ===")
    results = execute_complete_query(insert_chunks)
    print(f"Results shape: {results.shape}")
    print(results.head())

    # Export results to bulk folder
    print("\n=== EXPORTING RESULTS ===")
    export_path = export_results(results, folder_path_bulk)

    return export_path
