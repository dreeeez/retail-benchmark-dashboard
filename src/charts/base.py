"""
Benchmark Dashboard - Gruppe 18
Chart Base Configuration

Gemeinsames Layout für alle Charts.
"""


def get_base_layout(**kwargs) -> dict:
    """Basis-Layout für alle Plotly-Charts

    Args:
        **kwargs: Zusätzliche Layout-Parameter

    Returns:
        Layout-Dict für fig.update_layout()
    """
    base = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font_color': 'white',
        'transition': {'duration': 500},
    }
    base.update(kwargs)
    return base


def get_legend_horizontal() -> dict:
    """Standard-Legende horizontal oben"""
    return dict(orientation="h", yanchor="bottom", y=1.02)


def get_legend_horizontal_centered() -> dict:
    """Legende horizontal zentriert oben"""
    return dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
