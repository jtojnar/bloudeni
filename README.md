# Tools for Sudetské Tojnárkovo Bloudění

Various tools for organizing Sudetské Tojnárkovo Bloudění, a multi-day orienteering event in Sudeten.

https://bloudeni.krk-litvinov.cz/

## `vysledky.py`

Produces a results print-out using rogaining-style category ordering from an Excel spreadsheet containing a list of checkpoints visited by each team.

### Usage

Adjust `stages` variable in the `vysledky.py` file to change captions used in the print out as well as parameters for calculating score. The keys are used as file names of the used CSV files. `sheets` variable will map Excel sheet names to a CSV file names for an optional automated conversion of the Excel file to CSV files used by the script (requires `in2csv`program to be installed, comment out `csv_from_excel` invocation to disable).

The script will load `entries.csv` file in the `data/` directory to get information about teams (exported from [entries](https://github.com/jtojnar/entries) with the addition of `ignore` column containing `ms` value for teams to be counted as out of competition). It will also load `data/${stage_key}.csv` for each stage listed in the aforementioned `stages` variable. Running the script wll then produce results for each stages as well as the total result for all stages in the `out/` directory.
