"""Generate a visual timeline of lab-relevant venue deadlines and dates."""

import argparse
import datetime as dt

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from venue_data import VALID_SCOPES, date_span, load_venues


SCOPE_COLORS = {
    'core': '#2471a3',
    'adjacent': '#b9770e',
    'watch': '#7f8c8d',
}


def venue_label(venue):
    """Build a compact axis label with independent external rank signals."""
    signals = []
    if venue.get('ccf_rank'):
        signals.append(f'CCF {venue["ccf_rank"]}')
    if venue.get('icore_rank'):
        signals.append(f'ICORE {venue["icore_rank"]}')
    if not signals:
        signals.append('no external rank')
    return f'{venue["name"]}  [{" · ".join(signals)}]'


def plot_timeline(venues, output_path='conference_timeline.png', scope='core', show=True):
    venues = [venue for venue in venues if venue['conference'] is not None]
    venues.sort(
        key=lambda venue: min(
            (deadline['date'] for deadline in venue['deadlines']),
            default=venue['conference'],
        )
    )
    if not venues:
        raise ValueError(f'No scheduled conference events found for scope "{scope}".')

    first_date, last_date = date_span(venues)
    span_start = dt.date(first_date.year, 1, 1)
    span_end = dt.date(last_date.year, 12, 31)
    n = len(venues)
    fig, ax = plt.subplots(figsize=(18, max(6, n * 0.65 + 2)))

    for year in range(span_start.year + 1, span_end.year + 1):
        ax.axvline(dt.date(year, 1, 1), color='#555', linewidth=1.2,
                   linestyle='--', alpha=0.35, zorder=1)

    for i, venue in enumerate(venues):
        color = SCOPE_COLORS[venue['lab_scope']]
        deadlines = sorted(venue['deadlines'], key=lambda item: item['date'])
        conference = venue['conference']

        if deadlines:
            ax.hlines(i, deadlines[0]['date'], venue['conference_end'], colors=color,
                      linewidth=2.5, alpha=0.28, zorder=2)

        for deadline in deadlines:
            expected = deadline['status'] != 'confirmed'
            ax.scatter(
                deadline['date'], i, marker='D', s=65, zorder=4,
                facecolors='white' if expected else color,
                edgecolors=color, linewidths=1.4 if expected else 0.5,
            )
            ax.text(deadline['date'], i + 0.22,
                    deadline['date'].strftime('%-m/%-d'),
                    ha='center', va='bottom', fontsize=6.5, color=color, zorder=5)
            note = deadline.get('notes', '')
            short_note = note.split(';', 1)[0]
            if short_note and len(short_note) <= 18:
                ax.text(deadline['date'], i - 0.22, short_note,
                        ha='center', va='top', fontsize=5.5, color=color,
                        zorder=5, alpha=0.85, style='italic')

        conference_event = venue['conference_event']
        expected = conference_event['status'] != 'confirmed'
        ax.scatter(
            conference, i, marker='*', s=280, zorder=4,
            facecolors='white' if expected else color,
            edgecolors=color, linewidths=1.5 if expected else 0.5,
        )

    ax.set_yticks(range(n))
    ax.set_yticklabels([venue_label(venue) for venue in venues], fontsize=9)
    ax.set_ylim(-0.6, n + 0.2)
    ax.set_xlim(span_start, span_end)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
    plt.setp(ax.xaxis.get_majorticklabels(), ha='center', fontsize=8)
    ax.xaxis.grid(True, alpha=0.2, linestyle=':')
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)

    today = dt.date.today()
    if span_start <= today <= span_end:
        ax.axvline(today, color='green', linewidth=1.2, linestyle=':',
                   alpha=0.8, zorder=3)
        ax.text(today, -0.55, 'today', ha='center', va='top', fontsize=7,
                color='green', alpha=0.9)

    legend = [
        mpatches.Patch(color=color, label=f'{name.title()} lab scope')
        for name, color in SCOPE_COLORS.items()
        if scope == 'all' or name == scope
    ]
    legend += [
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#555',
               label='Paper deadline', markersize=8),
        Line2D([0], [0], marker='D', color='#555', markerfacecolor='white',
               label='Expected / unverified date', markersize=7, linestyle='None'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='#555',
               label='Venue start date', markersize=12),
    ]
    ax.legend(handles=legend, loc='upper left', fontsize=8,
              framealpha=0.9, edgecolor='#ccc')
    ax.set_title(f'HIL Venue Submission & Event Timeline  [{scope} scope]',
                 fontsize=13, fontweight='bold', pad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f'Saved to {output_path}')
    if show:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate the HIL venue submission and event timeline.')
    parser.add_argument('--scope', choices=(*VALID_SCOPES, 'all'), default='core',
                        help='Lab scope to include (default: core).')
    parser.add_argument('--show-all', action='store_true',
                        help='Compatibility alias for --scope all.')
    parser.add_argument('--venues', default='venues.csv',
                        help='Stable venue metadata CSV (default: venues.csv).')
    parser.add_argument('--events', default='events.csv',
                        help='Edition event CSV (default: events.csv).')
    parser.add_argument('--output', default='conference_timeline.png')
    parser.add_argument('--no-show', action='store_true')
    args = parser.parse_args()

    chosen_scope = 'all' if args.show_all else args.scope
    loaded = load_venues(args.venues, args.events, scope=chosen_scope)
    plot_timeline(loaded, output_path=args.output, scope=chosen_scope,
                  show=not args.no_show)
