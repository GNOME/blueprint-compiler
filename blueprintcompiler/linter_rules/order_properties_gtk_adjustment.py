from ..errors import CompileWarning
from ..language import Property
from .utils import LinterRule


class OrderPropertiesGtkAdjustment(LinterRule):
    id = "adjustment_prop_order"
    severity = "problem"
    category = "technical"

    def check(self, type, child, stack):
        properties = child.content.children[Property]
        preferred_order = ["lower", "upper", "value"]
        if type in type_order_properties:
            index = -1
            for property in properties:
                if property.name not in preferred_order:
                    continue
                new_index = preferred_order.index(property.name)
                if new_index < index:
                    self.problems.append(
                        CompileWarning(
                            f"{type} properties should be ordered as lower, upper, and then value.",
                            child.range,
                            id=self.id,
                        )
                    )
                    break
                index = new_index


type_order_properties = ["Gtk.Adjustment"]
