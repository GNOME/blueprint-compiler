from ..errors import CompileWarning, CodeAction
from ..language import Child, Property
from .utils import LinterRule
from ..utils import TextEdit


class PreferAdwBin(LinterRule):
    def check(self, type, child, stack):
        # rule suggestion/prefer-adwbin
        # FIXME: Only if use Adw is in scope and no Gtk.Box properties are used
        children = child.content.children[Child]
        if type == "Gtk.Box" and len(children) == 1:
            additional_edits = []
            if "Adw" not in child.root.gir.namespaces:
                additional_edits.append(
                    TextEdit(child.root.import_range("Adw"), f"\nusing Adw 1;")
                )

            for prop in child.content.children[Property]:
                if prop.name in (
                    "baseline-child",
                    "baseline-position",
                    "orientation",
                    "spacing",
                ):
                    additional_edits.append(
                        TextEdit(prop.range.with_preceding_whitespace, "")
                    )

            problem = CompileWarning(
                f"Use Adw.Bin instead of a Gtk.Box for a single child",
                child.signature_range,
                actions=[
                    CodeAction(
                        "Use Adw.Bin",
                        "Adw.Bin",
                        edit_range=child.class_name.range,
                        additional_edits=additional_edits,
                    )
                ],
            )
            self.problems.append(problem)
