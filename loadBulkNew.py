from datetime import datetime

import numpy as np
import pandas as pd

from fileConfig import _dtypeBulk


def load_bulk_file(_file_import, _file_season_ss, _file_season_fw, _file_weekly, _file_erp, _file_tc,
                   _file_season_3=None):
    # ---Check first row weekly -- empty

    def read_excel_with_header_detection(file_path, sheet_name=0, dtype=None):
        """
        Read Excel file and detect if first row is N/A, then use second row as header
        """
        # First, read just the first two rows to check the header
        temp_df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=2, header=None)

        # Check if first cell [0,0] is N/A, NaN, or similar
        first_cell = temp_df.iloc[0, 0]

        # Check for various forms of N/A
        if (pd.isna(first_cell) or
                str(first_cell).upper() in ['N/A', 'NA', 'NULL', '#N/A'] or
                first_cell == ''):

            print("First row appears to be N/A, using second row as header")
            # Use second row (index 1) as header
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=1, dtype=dtype)
        else:
            print("Using first row as header")
            # Use first row (index 0) as header (default)
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=0, dtype=dtype)

        return df

        # ----Concat 3 season

    def safe_concat_seasons(_tableSS, _tableFW, _tableSS_3=None):
        tables = [_tableSS, _tableFW]

        if _tableSS_3 is not None and not _tableSS_3.empty:
            tables.append(_tableSS_3)

        return pd.concat(tables, ignore_index=True)

        # ----Merge weekly - linesheet

    def merge_with_date_range(weekly_df, season_df):
        merged_list = []
        weekly_df['Schedule ex.Factory'] = pd.to_datetime(weekly_df['Schedule ex.Factory'], errors='coerce')
        season_df['Valid From (C)'] = pd.to_datetime(season_df['Valid From (C)'], errors='coerce')
        season_df['Valid To (C)'] = pd.to_datetime(season_df['Valid To (C)'], errors='coerce')

        for _, weekly_row in weekly_df.iterrows():
            # Find matching season rows for this weekly row
            matching_season = season_df[
                (season_df['Style'] == weekly_row['Style']) &
                (season_df['Article'] == weekly_row['Article']) &
                (season_df['Valid From (C)'] <= weekly_row['Schedule ex.Factory']) &
                (season_df['Valid To (C)'] >= weekly_row['Schedule ex.Factory'])
                ]

            if not matching_season.empty:
                # Create a merged row for EACH matching season record
                for _, season_row in matching_season.iterrows():
                    merged_row = {}
                    merged_row.update(weekly_row.to_dict())
                    merged_row.update(season_row.to_dict())
                    merged_list.append(merged_row)
            else:
                # No matching season data, add weekly row with NaN for season columns
                season_columns = ['Price', 'PriceA', 'Size', 'Valid From (C)', 'Valid To (C)']
                merged_row = weekly_row.to_dict()
                for col in season_columns:
                    if col not in merged_row:  # Only add if column doesn't exist
                        merged_row[col] = None
                merged_list.append(merged_row)

        # Create output DataFrame
        result_df = pd.DataFrame(merged_list)

        return result_df

    def update_fob_usa(row):
        row['PLANDATE'] = pd.to_datetime(row['PLANDATE'], errors='coerce')
        row['PODD'] = pd.to_datetime(row['PODD'], errors='coerce')
        row['FACPRICE'] = pd.to_numeric(row['FACPRICE'], errors='coerce')

        month = row['PLANDATE'].month if pd.notnull(row['PODD']) else row['PODD'].month
        country = row['SHIPTOCOUNTRY']

        price_map = {
            'USA': (0.9275, 0.9475),
            'MEX': (0.93, 0.95),
            'ARG': (0.93, 0.95),
            'RUS': (0.93, 0.95),
            'UKR': (0.93, 0.95),
            'IND': (0.93, 0.95)
        }

        if country in price_map:
            return row['FACPRICE'] * (price_map[country][0] if month >= 9 or month <= 2 else price_map[country][1])
        return row['FACPRICE']

        # --filter file season

    def get_filtered_table(df):
        return df[
            (df['Status (C)'].str.contains('Confirmed', case=False, na=False))].copy()
            # (df['Costsheet Status (C)'].str.contains('Confirmed', case=False, na=False))].copy()

    print('Start Processing...')
    # ----Read excel file
    _tableBulk = pd.read_excel(_file_import
                               , dtype=_dtypeBulk
                               , sheet_name='Sheet1'
                               )
    _tableBulk["TABLETYPE"]: int = 2
    _tableBulk["CREATEDBY"]: str = "AD"
    _tableSS = pd.read_excel(_file_season_ss, sheet_name='Sheet1', dtype={"Sizes Within Size Group (C)": str})
    _tableSS = _tableSS[_tableSS['Factory Group Code (MF)'] == '213001'].copy()
    _tableFW = pd.read_excel(_file_season_fw, sheet_name='Sheet1', dtype={"Sizes Within Size Group (C)": str})
    _tableFW = _tableFW[_tableFW['Factory Group Code (MF)'] == '213001'].copy()
    _tableWeekly = read_excel_with_header_detection(_file_weekly, sheet_name=0, dtype={"PO": str})
    _tableErp = pd.read_excel(_file_erp, sheet_name='Sheet1')
    _tableTC = pd.read_excel(_file_tc, sheet_name=0)
    _tableWeekly['Schedule ex.Factory'] = pd.to_datetime(_tableWeekly['Schedule ex.Factory']).dt.date

    _tableSS_3 = None
    if _file_season_3 is not None:
        _tableSS_3 = pd.read_excel(_file_season_3, sheet_name='Sheet1', dtype={"Sizes within Size Group (C)": str})
        _tableSS_3 = _tableSS_3[_tableSS_3['Factory Group Code (MF)'] == '213001'].copy()

    _filteredSelectionTC = _tableTC[
        ['PO Number', 'PO Line Aggregator', 'Price Per Unit', 'Technical Size', 'Article Number', 'Working Number',
         'Total Adjustments',
         'Total Document Amount']].copy()

    _filteredSelectionTC['PO Number'] = _filteredSelectionTC['PO Number'].apply(
        lambda x: '0' + str(x) if len(str(x)) == 9 else str(x)
    )

    _filteredSelectionTC.rename(
        columns={'PO Number': 'PO', 'Price Per Unit': 'PriceTC', 'Technical Size': 'Size', 'Article Number': 'Article',
                 'Working Number': 'Style'},
        inplace=True)
    _filteredSelectionTC['PO'] = _filteredSelectionTC['PO'].astype(str)
    _filteredSelectionTC['Size'] = _filteredSelectionTC['Size'].astype(str)

    _tableBulk.replace({pd.NA: "", float('nan'): "", float(
        'inf'): "", float('-inf'): ""}, inplace=True)

    _tableBulk = _tableBulk.drop_duplicates()

    _tableBulk['FOBPRICE'] = _tableBulk.apply(update_fob_usa, axis=1)

    # _resultImport = conn.import_json_to_db(_tableBulk)
    # print('Import Bulk Complete') if _resultImport else print('Import Bulk Errors')

    # ---filter weekly file current month +1 ---filter weekly file
    _now = datetime.today()
    _currentMonth = _now.month

    combinedSeason = safe_concat_seasons(_tableSS, _tableFW, _tableSS_3)

    combinedSeason = combinedSeason.drop_duplicates()

    combinedSeason['Valid From (C)'] = pd.to_datetime(combinedSeason['Valid From (C)'], errors='coerce')
    combinedSeason['Valid To (C)'] = pd.to_datetime(combinedSeason['Valid To (C)'], errors='coerce')

    _tableSeason = get_filtered_table(combinedSeason)


    # --Get the necessary columns in weekly, season and erp
    column_maps = {
        'weekly': {
            'columns': ['Style No/', 'Article Number', 'PO', 'Schedule ex.Factory'],
            'rename': {'Style No/': 'Style', 'Article Number': 'Article'}
        },
        'erp': {
            'columns': ['Sales order', 'Status', 'Remark', 'Customer requisition', 'PO Line Aggregator',
                        'Sales order type',
                        'Customer reference',
                        'Item number', 'Color', 'Style', 'Size', 'Quantity', 'Unit price', 'Fact price (Unit price)']
        },
        'season': {
            'columns': ['Working Number (M)', 'Intl. FOB (C)', 'Intl. Asian FOB (C)', 'Article Number (A)',
                        'Sizes Within Size Group (C)', 'Valid From (C)', 'Valid To (C)'],
            'rename': {'Working Number (M)': 'Style', 'Intl. FOB (C)': 'Price', 'Intl. Asian FOB (C)': 'PriceA',
                       'Article Number (A)': 'Article', 'Sizes Within Size Group (C)': 'Size'}
        }
    }

    _filteredWeekly = _tableWeekly[column_maps['weekly']['columns']].rename(
        columns=column_maps['weekly']['rename']).copy()

    _filteredErp = _tableErp[column_maps['erp']['columns']].copy()

    _filteredSeason = _tableSeason[column_maps['season']['columns']].rename(
        columns=column_maps['season']['rename']).copy()



    # ---Merged table
    _mergedTable = merge_with_date_range(_filteredWeekly, _filteredSeason)

    _mergedTable = _mergedTable.drop(
        columns=['Valid From (C)', 'Valid To (C)', 'Valid From (C)_x', 'Valid To (C)_x', 'Valid From (C)_y',
                 'Valid To (C)_y'], errors='ignore')


    _expandedTable = (
        _mergedTable
        .assign(Size=_mergedTable['Size'] .fillna('').astype(str).str.split(','))
        .explode('Size')
    )

    _expandedTable.rename(columns={'Style': 'Style1'}, inplace=True)

    _expandedTable['FinalPrice'] = _expandedTable.apply(
        lambda row: row['PriceA_y'] if 'A' in str(row['Size']) and pd.isnull(row['PriceA']) else
        row['PriceA'] if 'A' in str(row['Size']) else
        row['Price'],
        axis=1
    )
    _expandedTable = _expandedTable.drop(columns=['Price', 'PriceA', 'PriceA_x', 'PriceA_y'], errors='ignore')

    _expandedTable = _expandedTable.rename(columns={'FinalPrice': 'PriceLineSheet'})
    _expandedTable.reset_index(drop=True, inplace=True)

    _filteredErp['Customer reference'] = _filteredErp['Customer reference'].apply(
        lambda x: '0' + str(x) if len(str(x)) == 9 else str(x)
    )
    _filteredErp['Customer reference'] = _filteredErp['Customer reference'].astype(str)

    _filteredErp['PO Line Aggregator'] = _filteredErp['PO Line Aggregator'].replace('', np.nan)
    _filteredErp['PO Line Aggregator'] = _filteredErp['PO Line Aggregator'].fillna(1)
    _filteredErp['PO Line Aggregator'] = _filteredErp['PO Line Aggregator'].astype(int)

    _expandedTable['PO'] = _expandedTable['PO'].apply(
        lambda x: '0' + str(x) if len(str(x)) == 9 else str(x)
    )
    _expandedTable['PO'] = _expandedTable['PO'].astype(str)
    _filteredErp['Size'] = _filteredErp['Size'].astype(str)
    _expandedTable['Size'] = _expandedTable['Size'].astype(str)
    _tableMergedErp = pd.merge(
        _filteredErp,
        _expandedTable,
        left_on=['Item number', 'Color', 'Size', 'Customer reference'],
        right_on=['Style1', 'Article', 'Size', 'PO'],
        how='left'
    )
    _tableMergedErpTC = pd.merge(
        _tableMergedErp,
        _filteredSelectionTC,
        left_on=['Item number', 'Color', 'Size', 'Customer reference', 'PO Line Aggregator'],
        right_on=['Style', 'Article', 'Size', 'PO', 'PO Line Aggregator'],
        how='left'
    )
    # output_path = r'C:\Compare\Result\Test\Updated_Bulk2_{}.xlsx'.format(
    #     datetime.now().strftime('%Y%m%d%H%M%S')
    # )
    # _tableMergedErpTC.to_excel(output_path, index=False)

    _tableMergedErpTC.drop(columns=['Style1', 'Article_x', 'PO_x', 'PO_y', 'Article_y', 'Style_y'], inplace=True)
    _tableMergedErpTC = _tableMergedErpTC[~_tableMergedErpTC['Item number'].str.contains('ZRV', na=False)]

    _tableMergedErpTC['Result'] = _tableMergedErpTC.apply(
        lambda row: 'Match' if row['Fact price (Unit price)'] == row['PriceTC'] == row['PriceLineSheet']
        else 'Mismatch', axis=1)

    _tableMergedErpTC['Result1'] = _tableMergedErpTC.apply(
        lambda row: 'Match' if row['PriceLineSheet'] == row['PriceTC'] else 'Mismatch', axis=1)

    _tableMergedErpTC['Result2'] = _tableMergedErpTC.apply(
        lambda row: 'Match' if row['Fact price (Unit price)'] == row['PriceTC'] else 'Mismatch', axis=1)

    _tableMergedErpTC['PriceTC'] = _tableMergedErpTC['PriceTC'].astype('object')
    _tableMergedErpTC.loc[_tableMergedErpTC['PriceTC'] == 0.01, 'PriceTC'] = 'dummy price'

    return _tableMergedErpTC, _tableBulk
