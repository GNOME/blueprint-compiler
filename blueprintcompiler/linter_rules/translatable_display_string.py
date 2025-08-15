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
    (None, 'label'),
    (None, 'placeholder-text'),
    ('Gtk.Window', 'title'),
    ('Gtk.Entry', 'primary-icon-tooltip-markup'),
    ('Gtk.Entry', 'primary-icon-tooltip-text'),
    ('Gtk.Entry', 'secondary-icon-tooltip-markup'),
    ('Gtk.Entry', 'secondary-icon-tooltip-text'),
    ('Gtk.EntryBuffer', 'text'),
    ('Gtk.ListItem', 'accessible-description'),
    ('Gtk.ListItem', 'accessible-label'),
    ('Gtk.AboutDialog', 'comments'),
    ('Gtk.AboutDialog', 'translator-credits'),
    ('Gtk.AboutDialog', 'website-label'),
    ('Gtk.AlertDialog', 'detail'),
    ('Gtk.AlertDialog', 'message'),
    ('Gtk.AppChooserButton', 'heading'),
    ('Gtk.AppChooserDialog', 'heading'),
    ('Gtk.AppChooserWidget', 'default-text'),
    ('Gtk.AssistantPage', 'title'),
    ('Gtk.CellRendererText', 'markup'),
    ('Gtk.CellRendererText', 'text'),
    ('Gtk.ColorButton', 'title'),
    ('Gtk.ColorDialog', 'title'),
    ('Gtk.ColumnViewColumn', 'title'),
    ('Gtk.ColumnViewRow', 'accessible-description'),
    ('Gtk.ColumnViewRow', 'accessible-label'),
    ('Gtk.FileChooserNative', 'accept-label'),
    ('Gtk.FileChooserNative', 'cancel-label'),
    ('Gtk.FileDialog', 'accept-label'),
    ('Gtk.FileDialog', 'title'),
    ('Gtk.FileDialog', 'initial-name'),
    ('Gtk.FileFilter', 'name'),
    ('Gtk.FontButton', 'title'),
    ('Gtk.FontDialog', 'title'),
    ('Gtk.Inscription', 'markup'),
    ('Gtk.Inscription', 'text'),
    ('Gtk.LockButton', 'text-lock'),
    ('Gtk.LockButton', 'text-unlock'),
    ('Gtk.LockButton', 'tooltip-lock'),
    ('Gtk.LockButton', 'tooltip-not-authorized'),
    ('Gtk.LockButton', 'tooltip-unlock'),
    ('Gtk.MessageDialog', 'text'),
    ('Gtk.NotebookPage', 'menu-label'),
    ('Gtk.NotebookPage', 'tab-label'),
    ('Gtk.PrintDialog', 'accept-label'),
    ('Gtk.PrintDialog', 'title'),
    ('Gtk.Printer', 'name'),
    ('Gtk.PrintJob', 'title'),
    ('Gtk.PrintOperation', 'custom-tab-label'),
    ('Gtk.PrintOperation', 'export-filename'),
    ('Gtk.PrintOperation', 'job-name'),
    ('Gtk.ProgressBar', 'text'),
    ('Gtk.ShortcutLabel', 'disabled-text'),
    ('Gtk.ShortcutsGroup', 'title'),
    ('Gtk.ShortcutsSection', 'title'),
    ('Gtk.ShortcutsShortcut', 'title'),
    ('Gtk.ShortcutsShortcut', 'subtitle'),
    ('Gtk.StackPage', 'title'),
    ('Gtk.TextBuffer', 'text'),
    ('Gtk.TreeViewColumn', 'title')
]
