# Shamelessly ripped and modified from
# https://github.com/SublimeText/TrailingSpaces

import sublime
import sublime_plugin

DEFAULT_MAX_FILE_SIZE = 1048576
DEFAULT_COLOR_SCOPE_NAME = "invalid"
DEFAULT_COLOR_SCOPE_NAME_COOL = "invalid"
DEFAULT_FLAGS = sublime.DRAW_EMPTY
DEFAULT_FLAGS_COOL = sublime.DRAW_STIPPLED_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
DEFAULT_IS_ENABLED = True
DEFAULT_REGEX = '(\t+ +(?![*]))|( +\t+)|([\t ]+$)'
DEFAULT_REGEX_COOL = '[\u2026\u2018\u2019\u201c\u201d\u2013\u2014\u00a0\u3000]'
DEFAULT_DELAY = 3000
DEFAULT_SYNTAX_IGNORE = []
SETTINGS_FILE = 'highlighter.sublime-settings'

class Preferences:
    def load(self, settings):
        self.enabled = bool(settings.get('highlighter_enabled', DEFAULT_IS_ENABLED))
        self.regex = settings.get('highlighter_regex', DEFAULT_REGEX)
        self.regex_cool = settings.get('highlighter_regex_cool', DEFAULT_REGEX_COOL)
        self.max_size = settings.get('highlighter_max_file_size', DEFAULT_MAX_FILE_SIZE)
        self.color_scope_name = settings.get('highlighter_scope_name', DEFAULT_COLOR_SCOPE_NAME)
        self.color_scope_name_cool = settings.get('highlighter_scope_name_cool', DEFAULT_COLOR_SCOPE_NAME_COOL)
        self.delay = settings.get('highlighter_delay', DEFAULT_DELAY)
        self.syntax_ignore = settings.get('highlighter_syntax_ignore', DEFAULT_SYNTAX_IGNORE)
        self.save_settings_on_change = settings.get('highlighter_save_settings_on_change', (False))
        self.settings = settings

    def save(self):
        sublime.save_settings(SETTINGS_FILE)

Pref = Preferences()

# Override/Force highlighter_enabled option that read from settings file
class HighlighterToggleCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        settings = view.settings()
        enabled = settings.get('highlighter_enabled')
        if enabled == Pref.enabled:
            settings.set('highlighter_enabled', None)
            sublime.status_message("Force Highlighter: None")
        elif enabled is None:
            enabled = not Pref.enabled
            settings.set('highlighter_enabled', enabled)
            sublime.status_message("Force Highlighter: " + str(enabled))
        else:
            enabled = not enabled
            settings.set('highlighter_enabled', enabled)
            sublime.status_message("Force Highlighter: " + str(enabled))

        highlighter(view)
        if Pref.save_settings_on_change:
            Pref.settings.set('highlighter_enabled', enabled)
            Pref.save()

    def is_checked(self):
        view = self.window.active_view()
        settings = view.settings()
        return settings.get('highlighter_enabled', DEFAULT_IS_ENABLED)


def plugin_loaded():
    settings = sublime.load_settings(SETTINGS_FILE)
    Pref.load(settings)
    settings.add_on_change('reload', lambda: Pref.load(settings))
    for w in sublime.windows():
        for v in w.views():
            v.settings().erase('highlighter_prev_enabled')


# Determine if the view is a find results view.
def is_find_results(view):
    return view.settings().get('syntax') and \
        "Find Results" in view.settings().get('syntax')


# Returns True if the view should be ignored, False otherwise.
def ignore_view(view):
    view_syntax = view.settings().get('syntax')

    if not view_syntax:
        return False

    for syntax_ignore in Pref.syntax_ignore:
        if syntax_ignore in view_syntax:
            return True

    return False


# Return an array of regions matching regex.
def find_regexes(view):
    return view.find_all(Pref.regex)


def find_regexes_cool(view):
    return view.find_all(Pref.regex_cool)


# Highlight regex matches.
def highlighter(view):
    if view.size() <= Pref.max_size and not ignore_view(view) and not is_find_results(view):

        # print('highlighter: ', view.file_name())
        # Before view.settings().set() was called in [HighlighterToggleCommand], [enabled] is None
        enabled = view.settings().get('highlighter_enabled')
        if enabled or (enabled is None and Pref.enabled):
            scope = Pref.color_scope_name
            scope_cool = Pref.color_scope_name_cool
        else:
            scope = scope_cool = ""

        regions = find_regexes(view)
        regions_cool = find_regexes_cool(view)
        view.add_regions('HighlighterListener', regions, scope, "", DEFAULT_FLAGS)
        view.add_regions('HighlighterListenerCool', regions_cool, scope_cool, "", DEFAULT_FLAGS_COOL)


# Highlight matching regions.
class HighlighterListener(sublime_plugin.EventListener):
    def __init__(self):
        self.pending = 0

    def parse(self, view):
        self.pending = self.pending - 1
        if self.pending > 0:
            return
        if Pref.enabled:
            highlighter(view)

    def on_modified_async(self, view):
        if Pref.enabled:
            self.pending = self.pending + 1
            sublime.set_timeout(lambda: self.parse(view), Pref.delay)

    def on_activated_async(self, view):
        settings = view.settings()
        prev_enabled = settings.get('highlighter_prev_enabled')
        # highlighter_prev_enabled: previous [highlighter_enabled option read from settings file]
        # print('prev_enabled: {} -- Pref.enabled: {} -- File: {}'.format(prev_enabled, Pref.enabled, view.file_name()))
        if prev_enabled is None or prev_enabled != Pref.enabled:
            highlighter(view)
        settings.set('highlighter_prev_enabled', Pref.enabled)

# ST2 backwards compatibility
if int(sublime.version()) < 3000:
    plugin_loaded()
