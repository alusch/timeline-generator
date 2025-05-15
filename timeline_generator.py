import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import textwrap

def get_timeline(data, start=None, end=None,
                 granularity='hours', interval=24, minor_interval=None, dateformat='%a %b %d',
                 fig_height=None, fig_width=None, inches_per_xtick=1.5, inches_per_ytick=1.5,
                 rotate_labels=True, capstyle='round', default_style=None, styles=None,
                 hide_partially_visible_labels=False, filename=None):

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

    defaults = {
        'text_wrap': 50,
        'x_offset': 10,
        'x_offset_unit': 'points',
        'y_offset': 4,
        'y_offset_unit': 'points',
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

    if default_style:
        defaults = defaults | default_style

    if not styles:
        styles = {}

    data['options'] = data.apply(lambda row: compute_options(defaults, styles, row.options), axis=1)
    data_options = pd.DataFrame([x for x in data.options])
    data = data.combine_first(data_options)
    data = data.where(pd.notnull(data), None)

    spans = data[data.end_datetime.notnull()]
    if spans.shape[0] > 0:
        ax.hlines(spans.height, spans.start_datetime, spans.end_datetime,
                  linewidth=spans.linewidth, capstyle=capstyle, alpha=spans.alpha,
                  color=spans.color)
    milestones = data[data.end_datetime.isnull()]
    vlines = milestones[milestones.vline == True]
    plots = milestones[milestones.marker == True]
    for index, row in plots.iterrows():
        ax.plot(row.start_datetime, row.height, marker=row.markerfmt,
                color=row.color, markerfacecolor=row.color, markeredgewidth=row.markeredgewidth)
    ax.vlines(vlines.start_datetime, 0, vlines.height,
              color=vlines.color, linewidth=0.5)
    data.apply(lambda row: annotate(ax, row, inches_per_xtick, inches_per_ytick), axis=1)

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

    # Don't include axis tick labels in the size calculation so our automatic figure sizing always works
    ax.xaxis.set_in_layout(False)
    fig.tight_layout(pad = 0)

    # If desired, hide labels that were partially clipped by the above
    if hide_partially_visible_labels:
        axes_bbox = ax.get_window_extent()
        for label in ax.get_xticklabels():
            label_bbox = label.get_window_extent()
            if label_bbox.x0 < axes_bbox.x0 or label_bbox.x1 > axes_bbox.x1:
                label.set_visible(False)

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
        raise ValueError("invalid granularity " + granularity)

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
        raise ValueError("invalid granularity " + granularity)

def compute_options(defaults, base_options, specified):
    final_options = defaults
    base = specified.get('base')
    if isinstance(base, list):
        for b in base:
            final_options = compute_options(final_options, base_options, base_options.get(b, {}))
    elif base is not None:
        final_options = compute_options(final_options, base_options, base_options.get(base, {}))
    return final_options | specified

def convert_to_points(value, unit, inches_per_xtick, inches_per_ytick):
    if unit == 'points':
        return value
    elif unit == 'inches':
        return value * 72
    elif unit == 'xticks':
        return value * inches_per_xtick * 72
    elif unit == 'yticks':
        return value * inches_per_ytick * 72
    else:
        raise ValueError("unknown unit " + unit)

def annotate(ax, row, inches_per_xtick, inches_per_ytick):
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
    annotation = ax.annotate(
        description, xy=(anchor, row.height),
        xytext=(
            convert_to_points(row.x_offset, row.x_offset_unit, inches_per_xtick, inches_per_ytick),
            convert_to_points(row.y_offset, row.y_offset_unit, inches_per_xtick, inches_per_ytick)
        ),
        textcoords="offset points",
        horizontalalignment=row.horizontalalignment,
        verticalalignment="top",
        color=row.textcolor,
        arrowprops=row.arrowprops
    )

    # Don't include annotations in the size calculation so our automatic figure sizing always works
    annotation.set_in_layout(False)
