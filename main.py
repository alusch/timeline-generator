import argparse
import ast
import pathlib

import pandas as pd

import timeline_generator

def main():
    parser = argparse.ArgumentParser(description="Create a timeline from a CSV")
    parser.add_argument("in_file", metavar="CSV", type=pathlib.Path, help="Input CSV file")
    parser.add_argument("out_file", metavar="OUTPUT", type=pathlib.Path, help="Output image file to write")
    args = parser.parse_args()

    df = pd.read_csv(args.in_file)
    df['options'] = df['options'].apply(ast.literal_eval)
    timeline_generator.get_timeline(df, filename=args.out_file, granularity='years', interval=5, dateformat='%Y', minor_interval=1, rotate_labels=False)


if __name__ == "__main__":
    main()
