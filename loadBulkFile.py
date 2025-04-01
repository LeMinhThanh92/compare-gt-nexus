from datetime import datetime

import pandas as pd

import connection as conn
from fileConfig import _dtypeBulk


def load_bulk_file(_file_import, _file_season_ss, _file_season_fw, _file_weekly, _file_erp, _file_tc):
    _tableBulk = pd.read_excel(_file_import
                               , dtype=_dtypeBulk
                               , sheet_name='Sheet1'
                               )
    _tableBulk["TABLETYPE"]: int = 2
    _tableBulk["CREATEDBY"]: str = "AD"
    _tableSS = pd.read_excel(_file_season_ss, sheet_name='Sheet1')
    _tableSS = _tableSS[_tableSS['Factory Group Code (MF)'] == '213001'].copy()
    _tableFW = pd.read_excel(_file_season_fw, sheet_name='Sheet1')
    _tableFW = _tableFW[_tableFW['Factory Group Code (MF)'] == '213001'].copy()
    _tableWeekly = pd.read_excel(_file_weekly, sheet_name='MAR 2025')
    _tableErp = pd.read_excel(_file_erp, sheet_name='Sheet1')
    _tableTC = pd.read_excel(_file_tc, sheet_name='Page 1')

    _filteredSelectionTC = _tableTC[
        ['PO Number', 'Price Per Unit', 'Technical Size', 'Article Number', 'Working Number']].copy()
    _filteredSelectionTC.rename(
        columns={'PO Number': 'PO', 'Price Per Unit': 'PriceTC', 'Technical Size': 'Size', 'Article Number': 'Article',
                 'Working Number': 'Style'},
        inplace=True)
    _filteredSelectionTC['PO'] = _filteredSelectionTC['PO'].astype(str)
    _filteredSelectionTC['Size'] = _filteredSelectionTC['Size'].astype(str)

    _tableBulk.replace({pd.NA: "", float('nan'): "", float(
        'inf'): "", float('-inf'): ""}, inplace=True)

    _tableBulk = _tableBulk.drop_duplicates()

    # ---Update FOB in import file bulk

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

    _tableBulk['FOBPRICE'] = _tableBulk.apply(update_fob_usa, axis=1)

    _resultImport = conn.import_json_to_db(_tableBulk)
    print('Import Bulk Complete') if _resultImport else print('Import Bulk Errors')

    output_path = r'C:\Compare\Result\Bulk\Updated_Bulk_{}.xlsx'.format(
        datetime.now().strftime('%Y%m%d%H%M%S')
    )
    _tableBulk.to_excel(output_path, index=False)
    print(f"{datetime.now()} - Success Bulk. File saved to: {output_path}")
    # ---filter weekly file current month +1 ---filter weekly file
    _now = datetime.today()
    _currentMonth = _now.month

    # _currentYear = _now.year
    # # _currentMonth = (_now.month % 12)
    # # _currentYear = _now.year + (_currentMonth == 1)
    # _tableWeekly['Schedule ex.Factory'] = pd.to_datetime(_tableWeekly['Schedule ex.Factory'], errors='coerce')
    # _filterRow=_tableWeekly[_tableWeekly['Schedule ex.Factory'].dt.month == _currentMonth].copy()

    # --filter file season
    def get_filtered_table(df):
        return df[
            (df['Costsheet Status (C)'].str.contains('Confirmed', case=False, na=False)) &
            (df['Valid From (C)'] <= _now) &
            (df['Valid To (C)'] >= _now)
            ].copy()

    _tableFW['Valid From (C)'] = pd.to_datetime(_tableFW['Valid From (C)'], errors='coerce')
    _tableFW['Valid To (C)'] = pd.to_datetime(_tableFW['Valid To (C)'], errors='coerce')
    _tableSS['Valid From (C)'] = pd.to_datetime(_tableSS['Valid From (C)'], errors='coerce')
    _tableSS['Valid To (C)'] = pd.to_datetime(_tableSS['Valid To (C)'], errors='coerce')
    is_spring_summer_primary = 3 <= _currentMonth <= 8
    _tableSeason = get_filtered_table(_tableSS if is_spring_summer_primary else _tableFW)
    _tableSeason1 = get_filtered_table(_tableFW if is_spring_summer_primary else _tableSS)

    # --Get the necessary columns in weekly, season and erp
    column_maps = {
        'weekly': {
            'columns': ['Style No/', 'Article Number', 'PO'],
            'rename': {'Style No/': 'Style', 'Article Number': 'Article'}
        },
        'erp': {
            'columns': ['Sales order', 'Customer requisition', 'Sales order type', 'Customer reference',
                        'Item number', 'Color', 'Style', 'Size', 'Quantity', 'Unit price', 'Fact price (Unit price)']
        },
        'season': {
            'columns': ['Working Number (M)', 'Intl. FOB (C)', 'Intl. Asian FOB (C)', 'Article Number (A)',
                        'Sizes within Size Group (C)'],
            'rename': {'Working Number (M)': 'Style', 'Intl. FOB (C)': 'Price', 'Intl. Asian FOB (C)': 'PriceA',
                       'Article Number (A)': 'Article', 'Sizes within Size Group (C)': 'Size'}
        }
    }

    _filteredWeekly = _tableWeekly[column_maps['weekly']['columns']].rename(
        columns=column_maps['weekly']['rename']).copy()

    _filteredErp = _tableErp[column_maps['erp']['columns']].copy()

    _filteredSeason = _tableSeason[column_maps['season']['columns']].rename(
        columns=column_maps['season']['rename']).copy()

    _filteredSeason1 = _tableSeason1[column_maps['season']['columns']].rename(
        columns=column_maps['season']['rename']).copy()
    # ---Merged table
    _mergedTable = pd.merge(_filteredWeekly,
                            _filteredSeason,
                            left_on=['Style', 'Article'],
                            right_on=['Style', 'Article'],
                            how='left')

    _missingRows = _mergedTable[_mergedTable['Price'].isnull()]

    if not _missingRows.empty:
        filled_rows = pd.merge(
            _missingRows.drop(columns=['Price', 'Size']),
            _filteredSeason1,
            on=['Style', 'Article'],
            how='left'
        )

        _mergedTable = pd.concat([_mergedTable[~_mergedTable['Price'].isnull()], filled_rows])

    _expandedTable = (
        _mergedTable
        .assign(Size=_mergedTable['Size'].str.split(','))
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
    _expandedTable['PO'] = _expandedTable['PO'].astype(str)
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
        left_on=['Item number', 'Color', 'Size', 'Customer reference'],
        right_on=['Style', 'Article', 'Size', 'PO'],
        how='left'
    )
    # output_path = r'C:\Compare\Result\Bulk\size.xlsx'.format(
    #     datetime.now().strftime('%Y%m%d%H%M%S')
    # )
    # _filteredErp.to_excel(output_path, index=False)
    # print(f"{datetime.now()} - Success Bulk. File saved to: {output_path}")

    _tableMergedErpTC.drop(columns=['Style1', 'Article_x', 'PO_x', 'PO_y', 'Article_y', 'Style_y'], inplace=True)
    _tableMergedErpTC = _tableMergedErpTC[~_tableMergedErpTC['Item number'].str.contains('ZRV', na=False)]
    _tableMergedErpTC['Result'] = _tableMergedErpTC.apply(
        lambda row: 'Match' if row['Fact price (Unit price)'] == row['PriceTC'] == row['PriceLineSheet']
        else 'Mismatch', axis=1)

    return _tableMergedErpTC
