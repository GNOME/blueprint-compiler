from .avoid_all_caps import AvoidAllCaps
from .clamp_scrolledwindow import ClampScrolledWindow
from .incorrect_widget_placement import (
    IncorrectWidgetPlacement,
)
from .missing_user_facing_properties import (
    MissingUserFacingProperties,
)
from .no_gtk_switch_state import NoGtkSwitchState
from .no_visible_true import NoVisibleTrue
from .number_of_children import NumberOfChildren
from .order_properties_gtk_adjustment import (
    OrderPropertiesGtkAdjustment,
)
from .prefer_adw_bin import PreferAdwBin
from .prefer_unicode_chars import PreferUnicodeChars
from .require_a11y_label import RequireA11yLabel
from .translatable_display_string import (
    TranslatableDisplayString,
)
from .unused_object import UnusedObject
from .use_styles_over_css_classes import (
    UseStylesOverCssClasses,
)
from .utils import LinterRule

LINTER_RULES: list[type[LinterRule]] = [
    NumberOfChildren,
    PreferAdwBin,
    TranslatableDisplayString,
    NoGtkSwitchState,
    NoVisibleTrue,
    RequireA11yLabel,
    AvoidAllCaps,
    PreferUnicodeChars,
    MissingUserFacingProperties,
    UseStylesOverCssClasses,
    ClampScrolledWindow,
    IncorrectWidgetPlacement,
    OrderPropertiesGtkAdjustment,
    UnusedObject,
]
