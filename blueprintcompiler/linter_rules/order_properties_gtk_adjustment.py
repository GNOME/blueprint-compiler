from ..errors import CompileWarning
from ..language import Property
from .utils import LinterRule


class OrderPropertiesGtkAdjustment(LinterRule):
    def check(self, type, child, stack):
        properties = child.content.children[Property]
        preferred_order = ["lower", "upper", "value"]
        current_order = []
        if type in type_order_properties:
            for property in properties:
                current_order.append(property.name)
            if current_order != preferred_order:
                problem = CompileWarning(
                    f"{type} properties should be ordered as lower, upper, and then value.",
                    child.range,
                )
                self.problems.append(problem)


type_order_properties = ["Gtk.Adjustment"]
