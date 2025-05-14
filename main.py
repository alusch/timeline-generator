import argparse
import ast
import matplotlib
import matplotlib.markers as mmarkers
import matplotlib.text as mtext
import pathlib

import pandas as pd

import timeline_generator

SYMBOL_FONT = mtext.FontProperties(family="Segoe UI Symbol")

def main():
    parser = argparse.ArgumentParser(description="Create a timeline from a CSV")
    parser.add_argument("in_file", metavar="CSV", type=pathlib.Path, help="Input CSV file")
    parser.add_argument("out_file", metavar="OUTPUT", type=pathlib.Path, help="Output image file to write")
    args = parser.parse_args()

    df = pd.read_csv(args.in_file)
    df['options'] = df['options'].apply(ast.literal_eval)

    styles = {
        'axes.grid': True,
        'axes.grid.which': 'major',
        'grid.color': '#eeeeee',

        'font.family': ['Metropolis', 'Segoe UI Symbol'],
        'font.weight': 'medium',

        'xtick.labelsize': 16
    }
    matplotlib.rcParams.update(styles)

    defaults = {
        'linewidth': 22,
    }

    base_options = {
        'range': {
            'color': 'lightgray',
            'text_wrap': 300,
        },
        'range_annotated': {
            'base': 'range',
            'annotation_anchor': 'middle',
            'x_offset': 0,
            'y_offset': 0,
            'x_offset_unit': 'xticks',
            'y_offset_unit': 'yticks',
            'arrowprops': {
                'arrowstyle': '->',
                'connectionstyle': 'arc3,rad=0.1',
                'shrinkB': 0
            }
        },
        'ship': {
            'markerfmt': mmarkers.MarkerStyle(mtext.TextPath((-5, -3), '⛴', prop=SYMBOL_FONT)).scaled(2, 2),
        },
        'emigrated': {
            'base': 'ship',
            'placement': 'left',
            'vline': False,
        },
    }

    timeline_generator.get_timeline(df, filename=args.out_file, granularity='years', interval=5, dateformat='%Y', minor_interval=1, rotate_labels=False, capstyle='butt', inches_per_ytick=1, default_style=defaults, styles=base_options)


if __name__ == "__main__":
    main()
