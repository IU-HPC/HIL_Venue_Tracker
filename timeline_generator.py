import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import datetime as dt
import csv
from matplotlib.lines import Line2D

BASE_YEAR = 2026

TIER_COLORS = {
    'top':      '#c0392b',  # dark red
    'regular':  '#2980b9',  # blue
    'workshop': '#7f8c8d',  # gray
}


def load_conferences(csv_path):
    conferences = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            if name not in conferences:
                conferences[name] = {
                    'name': name,
                    'tier': row['tier'],
                    'deadlines': [],
                    'conference': None,
                }
            year = BASE_YEAR + int(row['year_offset'])
            date = dt.date(year, int(row['month']), int(row['day']))
            if row['event_type'] == 'conference':
                conferences[name]['conference'] = date
            else:
                conferences[name]['deadlines'].append(date)
    return list(conferences.values())


def plot_timeline(conferences):
    conferences.sort(key=lambda c: c['conference'])
    n = len(conferences)

    fig, ax = plt.subplots(figsize=(18, max(6, n * 0.6 + 2)))

    span_start = dt.date(BASE_YEAR - 1, 1, 1)
    year_boundary = dt.date(BASE_YEAR, 1, 1)
    span_end = dt.date(BASE_YEAR, 12, 31)

    # Shade the pre-year
    ax.axvspan(span_start, year_boundary, alpha=0.07, color='#e67e22', zorder=0)

    # Year boundary
    ax.axvline(year_boundary, color='#555', linewidth=1.5, linestyle='--', alpha=0.6, zorder=1)

    # Year labels at top
    ax.text(dt.date(BASE_YEAR - 1, 7, 1), n + 0.1, f'{BASE_YEAR - 1}  (pre-year)',
            ha='center', va='bottom', fontsize=11, color='#7d6608', alpha=0.8)
    ax.text(dt.date(BASE_YEAR, 7, 1), n + 0.1, f'{BASE_YEAR}  (main year)',
            ha='center', va='bottom', fontsize=11, color='#333', alpha=0.8)

    for i, conf in enumerate(conferences):
        color = TIER_COLORS[conf['tier']]
        deadlines = sorted(conf['deadlines'])
        conf_date = conf['conference']

        # Span line from earliest deadline to conference date
        if deadlines:
            ax.hlines(i, deadlines[0], conf_date, colors=color, linewidth=2.5,
                      alpha=0.3, zorder=2)

        # Deadline markers + tiny date labels
        for dl in deadlines:
            ax.scatter(dl, i, color=color, marker='D', s=65, zorder=4,
                       edgecolors='white', linewidths=0.5)
            ax.text(dl, i + 0.22, dl.strftime('%-m/%-d'),
                    ha='center', va='bottom', fontsize=6.5, color=color, zorder=5)

        # Conference marker
        ax.scatter(conf_date, i, color=color, marker='*', s=280, zorder=4,
                   edgecolors='white', linewidths=0.5)

    # Y axis
    ax.set_yticks(range(n))
    ax.set_yticklabels([c['name'] for c in conferences], fontsize=10)
    ax.set_ylim(-0.6, n + 0.2)

    # X axis: every month
    ax.set_xlim(span_start, span_end)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)

    # Vertical grid lines at each month
    ax.xaxis.grid(True, alpha=0.2, linestyle=':')
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)

    # Today marker
    today = dt.date.today()
    if span_start <= today <= span_end:
        ax.axvline(today, color='green', linewidth=1.2, linestyle=':', alpha=0.8, zorder=3)
        ax.text(today, -0.55, 'today', ha='center', va='top', fontsize=7,
                color='green', alpha=0.9)

    # Legend
    legend_elements = [
        mpatches.Patch(color=TIER_COLORS['top'],      label='Top Conference'),
        mpatches.Patch(color=TIER_COLORS['regular'],  label='Regular Conference'),
        mpatches.Patch(color=TIER_COLORS['workshop'], label='Workshop'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#555',
               label='Paper Deadline', markersize=8),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='#555',
               label='Conference Date', markersize=12),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8,
              framealpha=0.9, edgecolor='#ccc')

    ax.set_title(f'Conference Submission & Event Timeline  ({BASE_YEAR - 1}–{BASE_YEAR})',
                 fontsize=13, fontweight='bold', pad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('conference_timeline.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    confs = load_conferences('conferences.csv')
    plot_timeline(confs)

