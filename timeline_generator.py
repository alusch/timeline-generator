import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.markers as mmarkers
import matplotlib.text as mtext
import textwrap

SYMBOL_FONT = mtext.FontProperties(family="Segoe UI Symbol")


def get_timeline(data, start=None, end=None,
                 granularity='hours', interval=24, minor_interval=None, dateformat='%a %b %d',
                 fig_height=None, fig_width=None, inches_per_xtick=1.5, inches_per_ytick=1.5,
                 rotate_labels=True, filename=None):

    data['start_datetime'] = pd.to_datetime(data.start, format='mixed')
    data['end_datetime'] = pd.to_datetime(data.end, format='mixed')

    offset_args = {}
    offset_args[granularity] = interval
    if not start:
        start_datetime = data.start_datetime.min() - pd.DateOffset(**offset_args)
    else:
        start_datetime = pd.to_datetime(start)
    if not end:
        end_datetime = max(data.start_datetime.max(), data.end_datetime.max()) + pd.DateOffset(**offset_args)
    else:
        end_datetime = pd.to_datetime(end)

    if not fig_width:
        start_num = mdates.date2num(start_datetime)
        end_num = mdates.date2num(end_datetime)
        major_tick_size = mdates.RRuleLocator.get_unit_generic(get_freq(granularity)) * interval

        num_intervals = (end_num - start_num) / major_tick_size
        fig_width = num_intervals * inches_per_xtick

    valid_heights = data[
        ((data.start_datetime >= start_datetime) & (data.start_datetime <= end_datetime)) | 
        (pd.notnull(data.end_datetime) & (data.end_datetime >= start_datetime) & (data.end_datetime <= end_datetime))
    ].height

    min_height = min(0, valid_heights.min()) - 0.5
    max_height = valid_heights.max() + 0.5

    if not fig_height:
        fig_height = (max_height - min_height) * inches_per_ytick

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
    ax.set_xlim(start_datetime, end_datetime)
    ax.set_ylim(min_height, max_height)

    data['options'] = data.apply(lambda row: set_defaults(row.options), axis=1)
    data_options = pd.DataFrame([x for x in data.options])
    data = data.combine_first(data_options)
    data = data.where(pd.notnull(data), None)

    spans = data[data.end_datetime.notnull()]
    if spans.shape[0] > 0:
        ax.hlines(spans.height, spans.start_datetime, spans.end_datetime,
                  linewidth=spans.linewidth, capstyle='round', alpha=spans.alpha,
                  color=spans.color)
    milestones = data[data.end_datetime.isnull()]
    vlines = milestones[milestones.vline == True]
    plots = milestones[milestones.marker == True]
    for index, row in plots.iterrows():
        ax.plot(row.start_datetime, row.height, marker=row.markerfmt,
                color=row.color, markerfacecolor=row.color, markeredgewidth=row.markeredgewidth)
    ax.vlines(vlines.start_datetime, 0, vlines.height,
              color=vlines.color, linewidth=0.5)
    data.apply(lambda row: annotate(ax, row), axis=1)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_position('zero')
    ax.get_yaxis().set_ticks([])
    dtFmt = mdates.DateFormatter(dateformat)  # define the formatting
    ax.xaxis.set_major_formatter(dtFmt)
    ax.xaxis.set_major_locator(get_locator(granularity, interval))
    if (minor_interval):
        ax.xaxis.set_minor_locator(get_locator(granularity, minor_interval))

    if rotate_labels:
        fig.autofmt_xdate()

    fig.tight_layout(pad = 0)

    if (filename):
        plt.savefig(filename)
    return ax

def get_freq(granularity):
    if granularity == 'minutes':
        return mdates.MINUTELY
    elif granularity == 'hours':
        return mdates.HOURLY
    elif granularity == 'days':
        return mdates.DAILY
    elif granularity == 'weeks':
        return mdates.WEEKLY
    elif granularity == 'months':
        return mdates.MONTHLY
    elif granularity == 'years':
        return mdates.YEARLY
    else:
        raise "invalid granularity"

def get_locator(granularity, interval):
    if granularity == 'minutes':
        return mdates.MinuteLocator(interval=interval)
    elif granularity == 'hours':
        return mdates.HourLocator(interval=interval)
    elif granularity == 'days':
        return mdates.DayLocator(interval=interval)
    elif granularity == 'weeks':
        return mdates.RRuleLocator(mdates.rrulewrapper(mdates.WEEKLY, interval=interval))
    elif granularity == 'months':
        return mdates.MonthLocator(interval=interval)
    elif granularity == 'years':
        return mdates.YearLocator(base=interval)
    else:
        raise "invalid granularity"

def set_defaults(options):
    defaults = {
        'text_wrap': 50,
        'x_offset': 10,
        'y_offset': 5,
        'arrowprops': None,
        'annotation_anchor': 'left',
        'horizontalalignment': 'left',
        'color': 'darkblue',
        'textcolor': 'black',
        'alpha': 1,
        'linewidth': 20,
        'vline': True,
        'marker': True,
        'markerfmt': 'o',
        'markeredgewidth': 0,
        'placement':'right'
    }

    base_options = {
        'range': {
            'x_offset': 0,
            'color': 'lightgray',
            'text_wrap': 300,
        },
        'range_annotated': {
            'color': 'lightgray',
            'text_wrap': 300,
            'annotation_anchor': 'middle',
            'arrowprops': {
                'arrowstyle': '->',
                'connectionstyle': 'arc3,rad=0.1',
                'shrinkB': 0
            }
        },
        'emigrated': {
            'placement': 'left',
            'vline': False,
            'markerfmt': mmarkers.MarkerStyle(mtext.TextPath((-5, -3), '⛴', prop=SYMBOL_FONT)).scaled(2, 2),
        },
    }

    result = defaults | base_options.get(options.get('base'), {}) | options

    return result


def annotate(ax, row):
    description = "\n".join(textwrap.wrap(
        row.description, width=row['text_wrap']))
    if row['annotation_anchor'] == 'left':
        anchor = row['start_datetime']
    elif row['annotation_anchor'] == 'right':
        anchor = row['end_datetime']
    elif row['annotation_anchor'] == 'middle':
        start = mdates.date2num(row['start_datetime'])
        end = mdates.date2num(row['end_datetime'])
        avg = (start + end) / 2
        anchor = mdates.num2date(avg)
    elif row['annotation_anchor'] == 'start':
        anchor = mdates.num2date(ax.get_xlim()[0])
    elif row['annotation_anchor'] == 'end':
        anchor = mdates.num2date(ax.get_xlim()[1])
    if row['placement'] == 'left':
        row['horizontalalignment'] = 'right'
        row['x_offset'] = -10
    if pd.isna(row['arrowprops']):
        row['arrowprops'] = None
    ax.annotate(
        description, xy=(anchor, row.height),
        xytext=(row.x_offset, row.y_offset), 
        textcoords="offset points",
        horizontalalignment=row.horizontalalignment,
        verticalalignment="top",
        color=row.textcolor,
        arrowprops=row.arrowprops
    )
