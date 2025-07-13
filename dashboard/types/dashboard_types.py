#!/usr/bin/env python3
"""
Dashboard Type Definitions

Centralized type definitions for dashboard components.
Reduces duplication and ensures consistency across the codebase.

**Last Updated:** 2025-07-11 15:30:00
"""

from typing import Any, Dict, List, TypeAlias, Union

import panel as pn

# Common Panel component type aliases
PanelComponent: TypeAlias = Union[
    pn.pane.Bokeh, pn.pane.HTML, pn.Column, pn.Row, pn.Tabs, pn.widgets.Tabulator
]

BokehOrHTML: TypeAlias = Union[pn.pane.Bokeh, pn.pane.HTML]
ColumnOrHTML: TypeAlias = Union[pn.Column, pn.pane.HTML]

# Database result types
DatabaseTuple: TypeAlias = tuple[List[Any], int]
DatabaseResult: TypeAlias = Union[List[Any], DatabaseTuple]

# Widget value types
WidgetValue: TypeAlias = Union[str, int, float, bool, None]
FilterDict: TypeAlias = Dict[str, WidgetValue]

# Chart data types
ChartData: TypeAlias = Dict[str, List[Any]]
NodeData: TypeAlias = Dict[str, Union[List[float], List[str], List[int], List[bool]]]

# Component initialization parameters
ComponentParams: TypeAlias = Dict[str, Any]
