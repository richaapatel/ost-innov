from io import BytesIO

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
from django.http import HttpResponse

from exchanges.models import Exchange


PRIMARY = '#4361ee'
ACCENT = '#06d6a0'
MUTED = '#68738a'
INK = '#17213b'
GRID = '#e4e8f1'


def figure_to_png_response(fig):
    """Render a Matplotlib figure in memory and close it after serialization."""
    buffer = BytesIO()
    try:
        fig.tight_layout()
        fig.savefig(buffer, format='png', dpi=120, facecolor='white')
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Cache-Control'] = 'private, no-store'
        return response
    finally:
        plt.close(fig)
        buffer.close()


def _empty_figure(title, message):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.text(.5, .5, message, ha='center', va='center', color=MUTED, fontsize=11)
    ax.set_title(title, loc='left', color=INK, fontsize=14, fontweight='bold', pad=18)
    ax.set_axis_off()
    return fig


def build_skill_demand_figure(data):
    if not data:
        return _empty_figure('Skill demand', 'No skill demand data yet')
    labels = [item['label'] for item in data]
    values = [item['count'] for item in data]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    bars = ax.bar(labels, values, color=PRIMARY, width=.62)
    ax.set_title('Most requested skill categories', loc='left', color=INK, fontsize=14, fontweight='bold', pad=18)
    ax.set_xlabel('Skill category', color=MUTED)
    ax.set_ylabel('Learning goals', color=MUTED)
    ax.tick_params(axis='x', rotation=20, colors=MUTED)
    ax.tick_params(axis='y', colors=MUTED)
    ax.grid(axis='y', color=GRID, linewidth=.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value, str(value), ha='center', va='bottom', color=INK, fontsize=9, fontweight='bold')
    for spine in ('top', 'right', 'left'):
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    return fig


def build_exchange_status_figure(counts):
    labels = [label for _, label in Exchange.Status.choices]
    values = [counts.get(value, 0) for value, _ in Exchange.Status.choices]
    colors = ['#f4c95d', PRIMARY, '#ef476f', ACCENT]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    bars = ax.bar(labels, values, color=colors, width=.62)
    ax.set_title('Your exchange requests', loc='left', color=INK, fontsize=14, fontweight='bold', pad=18)
    ax.set_xlabel('Status', color=MUTED)
    ax.set_ylabel('Requests', color=MUTED)
    ax.tick_params(axis='x', colors=MUTED)
    ax.tick_params(axis='y', colors=MUTED)
    ax.grid(axis='y', color=GRID, linewidth=.8)
    ax.set_axisbelow(True)
    if not any(values):
        ax.text(.5, .9, 'There are currently no exchange requests', transform=ax.transAxes, ha='center', va='top', color=MUTED, fontsize=10)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value, str(value), ha='center', va='bottom', color=INK, fontsize=9, fontweight='bold')
    for spine in ('top', 'right', 'left'):
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    return fig
