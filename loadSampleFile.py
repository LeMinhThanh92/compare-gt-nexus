import os
from datetime import datetime
from decimal import Decimal

import pandas as pd

import connection as conn
from fileConfig import _dtypeSample


def load_sample_file(_file_import, _file_lo, _file_tc):
    _tableSample = pd.read_excel(_file_import
                                 , dtype=_dtypeSample
                                 , sheet_name='Sheet1'
                                 )
    _tableSample["TABLETYPE"]: int = 1
    _tableSample["CREATEDBY"]: str = "AD"

    _tableSample.replace({pd.NA: "", float('nan'): "", float(
        'inf'): "", float('-inf'): ""}, inplace=True)

    _filterRows = pd.read_excel(_file_lo, sheet_name=1)
    _tableLOAvg = pd.read_excel(_file_lo, sheet_name=2)
    _tableTC = pd.read_excel(_file_tc, sheet_name='Page 1')

    def check_filename_contains_monthly(file_path):
        filename = os.path.basename(file_path)
        return 'Monthly' in filename

    # _filterRows = _tableLO[_tableLO['FACTORY_NAME'] == '213001'].copy()
    _filterRowsAvg = _tableLOAvg[_tableLOAvg['FACTORY_NAME'] == '213001'].copy()

    STYLE = _filterRows.columns.values[2]
    FOB = _filterRows.columns.values[4]
    AVG = _filterRowsAvg.columns.values[3]
    AVG1 = _filterRowsAvg.columns.values[4]

    _filteredSelection = _filterRows[[STYLE, FOB]].copy()
    _filteredSelection.rename(columns={STYLE: 'STYLE', FOB: 'FOB'}, inplace=True)

    # _filteredSelection.loc[:,'FOB'] = _filteredSelection['FOB'] * value

    _filteredSelectionTC = _tableTC[['Working Number', 'Price Per Unit']].copy()
    _filteredSelectionTC.rename(columns={'Working Number': 'STYLE', 'Price Per Unit': 'TCFOB'}, inplace=True)

    _mergedTable = pd.merge(_tableSample,
                            _filteredSelection,
                            left_on='WORKNO',
                            right_on='STYLE',
                            how='left')
    _mergedTable.drop(columns=['STYLE'], inplace=True)
    _mergedTable.fillna(0, inplace=True)
    value = 2 if check_filename_contains_monthly(_file_import) else 1.53

    if value == 2:
        _mergedTable.loc[_mergedTable['FOB'] == 0, 'FOB'] = _filterRowsAvg[AVG1].values[0]
    elif value == 1.53:
        _mergedTable.loc[_mergedTable['FOB'] == 0, 'FOB'] = _filterRowsAvg[AVG].values[0]

    _mergedTable['FOB'] = _mergedTable['FOB'].apply(lambda x: Decimal(x).quantize(Decimal('0.00')))

    _mergedTable = pd.merge(_mergedTable,
                            _filteredSelectionTC,
                            left_on='WORKNO',
                            right_on='STYLE',
                            how='left')

    _mergedTable.drop(columns=['STYLE'], inplace=True)
    _mergedTable['TCFOB'] = _mergedTable['TCFOB'].apply(lambda x: Decimal(x).quantize(Decimal('0.00')))
    _mergedTable['Result'] = abs((_mergedTable['FOB'] - _mergedTable['TCFOB']) / _mergedTable['TCFOB'] * 100)
    _mergedTable['Result'] = _mergedTable['Result'].apply(lambda x: Decimal(x).quantize(Decimal('0.00')))

    _mergedTable.replace({pd.NA: "", float('nan'): "", float(
        'inf'): "", float('-inf'): ""}, inplace=True)
    _mergedTable = _mergedTable.drop_duplicates()

    # _jsonDataSample = _mergedTable.to_json(orient='records', date_format='iso', indent=4)

    _resultImport = conn.import_json_to_db(_mergedTable)
    _mergedTable.drop(columns=['TABLETYPE', 'CREATEDBY'], inplace=True)
    output_path = r'C:\Users\Admin\Downloads\Check price\Check price\Result\Sample\Updated_Sample_{}.xlsx'.format(
        datetime.now().strftime('%Y%m%d%H%M%S')
    )
    _mergedTable.to_excel(output_path, index=False)
    print(f"{datetime.now()} - Success Sample. File saved to: {output_path}")

    return 'Import Sample Complete' if _resultImport else 'Import Sample Errors'
