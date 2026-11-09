import os
from decimal import Decimal

import numpy as np
import pandas as pd

from fileConfig import _dtypeSample
from file_utils import smart_read_excel

TWO_PLACES = Decimal('0.00')


def _quantize_col(series: pd.Series) -> pd.Series:
    return series.map(lambda x: Decimal(x).quantize(TWO_PLACES))


def load_sample_file(_file_import, _file_lo, _file_tc):
    print('Start process sample')

    tc_cols = ['PO Number', 'Price Per Unit', 'Total Adjustments', 'Total Document Amount']
    sample_canonical_cols = ['ORDERNO', 'WORKNO', 'CUSTREQDATE']

    _tableSample = smart_read_excel(
        _file_import,
        dtype=_dtypeSample,
        sheet_name='Sheet1',
        canonical_cols=sample_canonical_cols
    )
    with pd.ExcelFile(_file_lo, engine='openpyxl') as xls:
        _filterRows = pd.read_excel(xls, sheet_name=1)
        _tableLOAvg = pd.read_excel(xls, sheet_name=2)

    _filteredSelectionTC = smart_read_excel(
        _file_tc,
        sheet_name=0,
        usecols=tc_cols
    )

    _tableSample["TABLETYPE"]: int = 1
    _tableSample["CREATEDBY"]: str = "AD"

    _tableSample.replace({pd.NA: "", float('nan'): "", float(
        'inf'): "", float('-inf'): ""}, inplace=True)

    def check_filename_contains_monthly(file_path):
        filename = os.path.basename(file_path)
        return 'Monthly' in filename

    # _filterRows = _tableLO[_tableLO['FACTORY_NAME'] == '213001'].copy()

    # _filterRowsAvg = _tableLOAvg[_tableLOAvg['FACTORY_NAME'].astype(str) == '213001'].copy()
    _filterRowsAvg = _tableLOAvg

    STYLE = _filterRows.columns.values[2]
    FOB = _filterRows.columns.values[4]
    AVG = _filterRowsAvg.columns.values[3]
    AVG1 = _filterRowsAvg.columns.values[4]

    _filteredSelection = _filterRows[[STYLE, FOB]].rename(columns={STYLE: 'STYLE', FOB: 'FOB'})

    print('load avg')

    # _filteredSelection.loc[:,'FOB'] = _filteredSelection['FOB'] * value

    _filteredSelectionTC.rename(columns={'PO Number': 'PO', 'Price Per Unit': 'TCFOB'}, inplace=True)

    s_orderno = _tableSample['ORDERNO'].astype(str)
    _tableSample['ORDERNO'] = np.where(s_orderno.str.len() == 9, '0' + s_orderno, s_orderno)
    _tableSample['ORDERNO'] = _tableSample['ORDERNO'].astype(str)
    _filteredSelectionTC['PO'] = _filteredSelectionTC['PO'].astype(str)

    _mergedTable = pd.merge(_tableSample,
                            _filteredSelection,
                            left_on='WORKNO',
                            right_on='STYLE',
                            how='left')
    _mergedTable.drop(columns=['STYLE'], inplace=True)
    _mergedTable.fillna(0, inplace=True)
    value = 2 if check_filename_contains_monthly(_file_import) else 1.53

    # output_path = r'C:\Compare\test.xlsx'
    # _mergedTable.to_excel(output_path, index=False)
    # output_path = r'C:\Compare\test1.xlsx'
    # _filterRowsAvg.to_excel(output_path, index=False)
    # output_path = r'C:\Compare\test2.xlsx'
    # _tableLOAvg.to_excel(output_path, index=False)

    if value == 2:
        _mergedTable.loc[_mergedTable['FOB'] == 0, 'FOB'] = _filterRowsAvg[AVG1].values[0]
    elif value == 1.53:
        _mergedTable.loc[_mergedTable['FOB'] == 0, 'FOB'] = _filterRowsAvg[AVG].values[0]

    _mergedTable['FOB'] = _quantize_col(_mergedTable['FOB'])

    _mergedTable = pd.merge(_mergedTable,
                            _filteredSelectionTC,
                            left_on='ORDERNO',
                            right_on='PO',
                            how='left')

    _mergedTable.drop(columns=['PO'], inplace=True, errors='ignore')
    _mergedTable['TCFOB'] = _quantize_col(_mergedTable['TCFOB'])
    _mergedTable['Total Adjustments'] = _quantize_col(_mergedTable['Total Adjustments'])
    _mergedTable['Total Document Amount'] = _quantize_col(_mergedTable['Total Document Amount'])
    _mergedTable['Result'] = abs((_mergedTable['TCFOB'] - _mergedTable['FOB']) / _mergedTable['FOB'] * 100)
    _mergedTable['Result'] = _quantize_col(_mergedTable['Result'])

    _mergedTable.replace({pd.NA: "", float('nan'): "", float(
        'inf'): "", float('-inf'): ""}, inplace=True)
    _mergedTable = _mergedTable.drop_duplicates()

    # _jsonDataSample = _mergedTable.to_json(orient='records', date_format='iso', indent=4)

    # _resultImport = conn.import_json_to_db(_mergedTable)
    _mergedTable.drop(columns=['TABLETYPE', 'CREATEDBY'], inplace=True)
    # output_path = r'C:\Compare\Result\Sample\Updated_Sample_{}.xlsx'.format(
    #     datetime.now().strftime('%Y%m%d%H%M%S')
    # )
    # _mergedTable.to_excel(output_path, index=False)
    # print(f"{datetime.now()} - Success Sample. File saved to: {output_path}")

    return _mergedTable
