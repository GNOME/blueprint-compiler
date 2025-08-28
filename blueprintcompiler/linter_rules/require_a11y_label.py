from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.gtk_a11y import ExtAccessibility
from blueprintcompiler.linter_rules.utils import LinterRule


class RequireA11yLabel(LinterRule):
    def check(self, type, child, stack):
        # rule suggestion/require-a11y-label
        properties = child.content.children[Property]
        if type == "Gtk.Button":
            label = None
            tooltip_text = None
            accessibility_label = False

            # FIXME: Check what ATs actually do

            for property in properties:
                if property.name == "label":
                    label = property.value
                elif property.name == "tooltip-text":
                    tooltip_text = property.value

            accessibility__child = child.content.children[ExtAccessibility]
            if len(accessibility__child) > 0:
                accessibility_properties = child.content.children[ExtAccessibility][
                    0
                ].properties
                for accessibility_property in accessibility_properties:
                    if accessibility_property.name == "label":
                        accessibility_label = True

            if label is None and tooltip_text is None and accessibility_label is False:
                problem = CompileWarning(
                    f"{type} is missing an accessibility label", child.range
                )
                self.problems.append(problem)

        # rule suggestion/require-a11y-label
        elif type == "Gtk.Image" or type == "Gtk.Picture":
            accessibility_label = False

            accessibility__child = child.content.children[ExtAccessibility]
            if len(accessibility__child) > 0:
                accessibility_properties = child.content.children[ExtAccessibility][
                    0
                ].properties
                for accessibility_property in accessibility_properties:
                    if accessibility_property.name == "label":
                        accessibility_label = True

            if accessibility_label is False:
                problem = CompileWarning(
                    f"{type} is missing an accessibility label", child.range
                )
                self.problems.append(problem)
