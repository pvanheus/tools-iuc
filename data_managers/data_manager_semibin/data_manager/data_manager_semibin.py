#!/usr/bin/env python
#
# Data manager for reference data for the MetaPhlAn Galaxy tools
import argparse
import json
import subprocess
from datetime import date
from pathlib import Path


# Utility functions for interacting with Galaxy JSON
def read_input_json(json_fp):
    """Read the JSON supplied from the data manager tool

    Returns a tuple (param_dict,extra_files_path)

    'param_dict' is an arbitrary dictionary of parameters
    input into the tool; 'extra_files_path' is the path
    to a directory where output files must be put for the
    receiving data manager to pick them up.

    NB the directory pointed to by 'extra_files_path'
    doesn't exist initially, it is the job of the script
    to create it if necessary.

    """
    with open(json_fp) as fh:
        params = json.load(fh)
    return (params['param_dict'],
            Path(params['output_data'][0]['extra_files_path']))


# Utility functions for creating data table dictionaries
#
# Example usage:
# >>> d = create_data_tables_dict()
# >>> add_data_table(d,'my_data')
# >>> add_data_table_entry(dict(dbkey='hg19',value='human'))
# >>> add_data_table_entry(dict(dbkey='mm9',value='mouse'))
# >>> print(json.dumps(d))
def create_data_tables_dict():
    """Return a dictionary for storing data table information

    Returns a dictionary that can be used with 'add_data_table'
    and 'add_data_table_entry' to store information about a
    data table. It can be converted to JSON to be sent back to
    the data manager.

    """
    d = {
        'data_tables': {}
    }
    return d


def add_data_table(d, table):
    """Add a data table to the data tables dictionary

    Creates a placeholder for a data table called 'table'.

    """
    d['data_tables'][table] = []


def add_data_table_entry(d, table, entry):
    """Add an entry to a data table

    Appends an entry to the data table 'table'. 'entry'
    should be a dictionary where the keys are the names of
    columns in the data table.

    Raises an exception if the named data table doesn't
    exist.

    """
    try:
        d['data_tables'][table].append(entry)
    except KeyError:
        raise Exception("add_data_table_entry: no table '%s'" % table)


def download_gtdb(data_tables, table_name, target_dp, test=False):
    """Download GTDB

    Creates references to the specified file(s) on the Galaxy
    server in the appropriate data table (determined from the
    file extension).

    The 'data_tables' dictionary should have been created using
    the 'create_data_tables_dict' and 'add_data_table' functions.

    Arguments:
      data_tables: a dictionary containing the data table info
      table_name: name of the table
      target_dp: directory to put copy or link to the data file

    """
    db_dp = target_dp
    if not test:
        cmd = "SemiBin download_GTDB --reference-db-data-dir %s" % (db_dp)
        subprocess.check_call(cmd, shell=True)
        dbkey = 'gtdb'
        name = "GTDB reference genome generated by MMseqs2 used in SemiBin"
    else:
        dbkey = 'test'
        name = "Test"
        empty_fp = db_dp / Path("empty")
        empty_fp.touch()
    add_data_table_entry(
        data_tables,
        table_name,
        dict(
            dbkey=dbkey,
            value='%s' % (date.today().strftime("%d%m%Y")),
            name=name,
            path=str(db_dp)))


if __name__ == "__main__":
    print("Starting...")

    # Read command line
    parser = argparse.ArgumentParser(description='Download reference genomes (GTDB)')
    parser.add_argument('--json', help="Path to JSON file")
    parser.add_argument('--test', action='store_true', help="Test")
    args = parser.parse_args()
    print("args   : %s" % args)

    # Read the input JSON
    json_fp = Path(args.json)
    params, target_dp = read_input_json(json_fp)

    # Make the target directory
    print("Making %s" % target_dp)
    target_dp.mkdir(parents=True, exist_ok=True)

    # Set up data tables dictionary
    data_tables = create_data_tables_dict()
    add_data_table(data_tables, "gtdb")

    # Fetch data from specified data sources
    print("Download and build database")
    download_gtdb(
        data_tables,
        "gtdb",
        target_dp,
        args.test)

    # Write output JSON
    print("Outputting JSON")
    with open(json_fp, 'w') as fh:
        json.dump(data_tables, fh, sort_keys=True)
    print("Done.")
