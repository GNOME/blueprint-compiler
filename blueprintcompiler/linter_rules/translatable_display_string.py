from blueprintcompiler.linter_rules.utils import LinterRule
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated
from blueprintcompiler.errors import CompileWarning

class TranslatableDisplayString(LinterRule):
    def check(self, type, child, stack):
        # rule suggestion/translatable-display-string
        properties = child.content.children[Property]
        for translatable_property in translatable_properties:
            if type == translatable_property[0] or translatable_property[0] == None:
                for property in properties:
                    if (property.name == translatable_property[1]):
                        value = property.children[0].child
                        if (not isinstance(value, Translated)):
                            range = value.range
                            problem = CompileWarning(f'Mark {type} {property.name} as translatable using _("...")', range)
                            self.problems.append(problem)

translatable_properties = [
    (None, 'tooltip-text'),
    ('Gtk.Label', 'label'),
    ('Gtk.Window', 'title'),
    ('Gtk.Button', 'label')
]
