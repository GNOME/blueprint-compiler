from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.linter_rules.utils import LinterRule


class OrderPropertiesGtkAdjustment(LinterRule):
    def check(self, type, child, stack):
        properties = child.content.children[Property]
        preferred_order = ["lower", "upper", "value"]
        current_order = []
        for property in properties:
            #  Ensure property is 'adjustment'
            if property.name in type_order_properties:
                adjustment_name = property.children[0].children[0].class_name.as_string
                adjustment_list = (
                    property.children[0].children[0].content.children[Property]
                )
                #  Ensure widget used is 'Adjustment'
                if adjustment_name in type_order_properties[property.name]:
                    for prop in adjustment_list:
                        current_order.append(prop.name)
                    if current_order != preferred_order:
                        problem = CompileWarning(
                            f"Gtk.{adjustment_name} properties should be ordered as lower, upper, and then value.",
                            child.range,
                        )
                        self.problems.append(problem)


type_order_properties = {"adjustment": ["Adjustment"]}
