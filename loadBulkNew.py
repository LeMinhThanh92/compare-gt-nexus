from datetime import datetime

import numpy as np
import pandas as pd

from fileConfig import _dtypeBulk
from file_utils import read_excel_with_header_detection, smart_read_excel


def load_bulk_file(_file_import, _file_season_ss, _file_season_fw, _file_weekly, _file_erp, _file_tc,
                   _file_season_3=None):
    # ----Concat 3 season

    def safe_concat_seasons(_tableSS, _tableFW, _tableSS_3=None):
        tables = [_tableSS, _tableFW]

        if _tableSS_3 is not None and not _tableSS_3.empty:
            tables.append(_tableSS_3)

        return pd.concat(tables, ignore_index=True)

    # ----Merge weekly - linesheet

    def merge_with_date_range(weekly_df, season_df):
        weekly_df = weekly_df.copy()
        season_df = season_df.copy()
        weekly_df['Schedule ex.Factory'] = pd.to_datetime(weekly_df['Schedule ex.Factory'], errors='coerce')
        season_df['Valid From (C)'] = pd.to_datetime(season_df['Valid From (C)'], errors='coerce')
        season_df['Valid To (C)'] = pd.to_datetime(season_df['Valid To (C)'], errors='coerce')

        season_columns = ['Price', 'PriceA', 'Size', 'Valid From (C)', 'Valid To (C)']
        out_cols = list(weekly_df.columns) + [c for c in season_columns if c not in weekly_df.columns]

        if weekly_df.empty:
            return pd.DataFrame(columns=out_cols)

        weekly_df['_w_idx'] = np.arange(len(weekly_df))
        season_df['_s_idx'] = np.arange(len(season_df))

        w_valid = weekly_df[['_w_idx', 'Style', 'Article', 'Schedule ex.Factory']][
            weekly_df['Style'].notna() & weekly_df['Article'].notna()
        ]
        s_valid = season_df[season_df['Style'].notna() & season_df['Article'].notna()]

        joined = pd.merge(w_valid, s_valid, on=['Style', 'Article'], how='inner')
        matching_season = joined[
            (joined['Valid From (C)'] <= joined['Schedule ex.Factory']) &
            (joined['Valid To (C)'] >= joined['Schedule ex.Factory'])
        ].sort_values(['_w_idx', '_s_idx'], kind='mergesort')

        if matching_season.empty:
            result_df = weekly_df.drop(columns=['_w_idx']).copy()
            for col in season_columns:
                if col not in result_df.columns:
                    result_df[col] = None
            return result_df[out_cols].reset_index(drop=True)

        result_df = pd.merge(
            weekly_df,
            matching_season[['_w_idx'] + season_columns],
            on='_w_idx',
            how='left'
        ).drop(columns=['_w_idx'])

        return result_df[out_cols].reset_index(drop=True)

    def update_fob_usa_vectorized(df):
        plandate = pd.to_datetime(df['PLANDATE'], errors='coerce')
        podd = pd.to_datetime(df['PODD'], errors='coerce')
        facprice = pd.to_numeric(df['FACPRICE'], errors='coerce')

        # Preserve exact existing logic: month = row['PLANDATE'].month if pd.notnull(row['PODD']) else row['PODD'].month
        month = np.where(podd.notna(), plandate.dt.month, podd.dt.month)
        is_sep_to_feb = (month >= 9) | (month <= 2)

        country = df['SHIPTOCOUNTRY']
        is_usa = country == 'USA'
        is_other = country.isin(['MEX', 'ARG', 'RUS', 'UKR', 'IND'])

        multiplier = np.select(
            [
                is_usa & is_sep_to_feb,
                is_usa & ~is_sep_to_feb,
                is_other & is_sep_to_feb,
                is_other & ~is_sep_to_feb,
            ],
            [0.9275, 0.9475, 0.93, 0.95],
            default=1.0
        )

        return np.where(is_usa | is_other, facprice * multiplier, facprice)

    # --filter file season

    def get_filtered_table(df):
        return df[
            (df['Status (C)'].str.contains('Confirmed', case=False, na=False))].copy()
        # (df['Costsheet Status (C)'].str.contains('Confirmed', case=False, na=False))].copy()

    def pad_po_9(series):
        s = series.astype(str)
        return np.where(s.str.len() == 9, '0' + s, s)

    print('Start Processing...')

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

    tc_columns = [
        'PO Number', 'PO Line Aggregator', 'Price Per Unit', 'Technical Size',
        'Article Number', 'Working Number', 'Total Adjustments', 'Total Document Amount'
    ]
    season_canonical_cols = ['Factory Group Code (MF)', 'Status (C)'] + column_maps['season']['columns']
    season_dtype = {"Sizes Within Size Group (C)": str}
    bulk_canonical_cols = ['PLANDATE', 'PODD', 'FACPRICE', 'SHIPTOCOUNTRY', 'FOBPRICE']

    # ----Read excel files with automatic column & sheet normalization
    _tableBulk = smart_read_excel(
        _file_import,
        dtype=_dtypeBulk,
        sheet_name='Sheet1',
        canonical_cols=bulk_canonical_cols
    )
    _tableBulk["TABLETYPE"]: int = 2
    _tableBulk["CREATEDBY"]: str = "AD"

    _tableSS = smart_read_excel(
        _file_season_ss,
        sheet_name='Sheet1',
        dtype=season_dtype,
        canonical_cols=season_canonical_cols
    )
    _tableSS = _tableSS[_tableSS['Factory Group Code (MF)'] == '213001'].copy()

    _tableFW = smart_read_excel(
        _file_season_fw,
        sheet_name='Sheet1',
        dtype=season_dtype,
        canonical_cols=season_canonical_cols
    )
    _tableFW = _tableFW[_tableFW['Factory Group Code (MF)'] == '213001'].copy()

    _tableWeekly = read_excel_with_header_detection(
        _file_weekly,
        sheet_name=0,
        dtype={"PO": str},
        usecols=column_maps['weekly']['columns']
    )

    _tableErp = smart_read_excel(
        _file_erp,
        sheet_name='Sheet1',
        usecols=column_maps['erp']['columns']
    )

    _filteredSelectionTC = smart_read_excel(
        _file_tc,
        sheet_name=0,
        usecols=tc_columns
    )

    _tableWeekly['Schedule ex.Factory'] = pd.to_datetime(_tableWeekly['Schedule ex.Factory']).dt.date

    _tableSS_3 = None
    if _file_season_3 is not None:
        _tableSS_3 = smart_read_excel(
            _file_season_3,
            sheet_name='Sheet1',
            dtype=season_dtype,
            canonical_cols=season_canonical_cols
        )
        _tableSS_3 = _tableSS_3[_tableSS_3['Factory Group Code (MF)'] == '213001'].copy()

    _filteredSelectionTC['PO Number'] = pad_po_9(_filteredSelectionTC['PO Number'])

    _filteredSelectionTC.rename(
        columns={'PO Number': 'PO', 'Price Per Unit': 'PriceTC', 'Technical Size': 'Size', 'Article Number': 'Article',
                 'Working Number': 'Style'},
        inplace=True)
    _filteredSelectionTC['PO'] = _filteredSelectionTC['PO'].astype(str)
    _filteredSelectionTC['Size'] = _filteredSelectionTC['Size'].astype(str)

    _tableBulk.replace({pd.NA: "", float('nan'): "", float(
        'inf'): "", float('-inf'): ""}, inplace=True)

    _tableBulk = _tableBulk.drop_duplicates()

    _tableBulk['FOBPRICE'] = update_fob_usa_vectorized(_tableBulk)

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

    _filteredWeekly = _tableWeekly.rename(
        columns=column_maps['weekly']['rename']).copy()

    _filteredErp = _tableErp

    _filteredSeason = _tableSeason[column_maps['season']['columns']].rename(
        columns=column_maps['season']['rename']).copy()

    # ---Merged table
    _mergedTable = merge_with_date_range(_filteredWeekly, _filteredSeason)

    _mergedTable = _mergedTable.drop(
        columns=['Valid From (C)', 'Valid To (C)', 'Valid From (C)_x', 'Valid To (C)_x', 'Valid From (C)_y',
                 'Valid To (C)_y'], errors='ignore')

    _expandedTable = (
        _mergedTable
        .assign(Size=_mergedTable['Size'].fillna('').astype(str).str.split(','))
        .explode('Size')
    )

    _expandedTable.rename(columns={'Style': 'Style1'}, inplace=True)

    has_a_in_size = _expandedTable['Size'].astype(str).str.contains('A', regex=False, na=False)
    if 'PriceA_y' in _expandedTable.columns:
        price_a_col = np.where(_expandedTable['PriceA'].isna(), _expandedTable['PriceA_y'], _expandedTable['PriceA'])
    else:
        price_a_col = _expandedTable['PriceA']

    _expandedTable['FinalPrice'] = np.where(has_a_in_size, price_a_col, _expandedTable['Price'])
    _expandedTable = _expandedTable.drop(columns=['Price', 'PriceA', 'PriceA_x', 'PriceA_y'], errors='ignore')

    _expandedTable = _expandedTable.rename(columns={'FinalPrice': 'PriceLineSheet'})
    _expandedTable.reset_index(drop=True, inplace=True)

    _filteredErp['Customer reference'] = pad_po_9(_filteredErp['Customer reference']).astype(str)

    _filteredErp['PO Line Aggregator'] = _filteredErp['PO Line Aggregator'].replace('', np.nan)
    _filteredErp['PO Line Aggregator'] = _filteredErp['PO Line Aggregator'].fillna(1)
    _filteredErp['PO Line Aggregator'] = _filteredErp['PO Line Aggregator'].astype(int)

    _expandedTable['PO'] = pad_po_9(_expandedTable['PO']).astype(str)
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
    _tableMergedErpTC = _tableMergedErpTC[~_tableMergedErpTC['Item number'].str.contains('ZRV', na=False)].copy()

    match_linesheet_tc = _tableMergedErpTC['PriceLineSheet'] == _tableMergedErpTC['PriceTC']
    match_fact_tc = _tableMergedErpTC['Fact price (Unit price)'] == _tableMergedErpTC['PriceTC']

    _tableMergedErpTC['Result'] = np.where(match_fact_tc & match_linesheet_tc, 'Match', 'Mismatch')
    _tableMergedErpTC['Result1'] = np.where(match_linesheet_tc, 'Match', 'Mismatch')
    _tableMergedErpTC['Result2'] = np.where(match_fact_tc, 'Match', 'Mismatch')

    _tableMergedErpTC['PriceTC'] = _tableMergedErpTC['PriceTC'].astype('object')
    _tableMergedErpTC.loc[_tableMergedErpTC['PriceTC'] == 0.01, 'PriceTC'] = 'dummy price'

    return _tableMergedErpTC, _tableBulk
