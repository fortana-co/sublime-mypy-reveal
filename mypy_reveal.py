try:
    from typing import Any, Tuple, Optional, cast
except Exception:
    cast = lambda t, v: v

import os
import string
import logging
import threading
import subprocess

import sublime  # type: ignore
import sublime_plugin  # type: ignore


def log(s: str) -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("mypy_reveal_type: {}".format(s))


def parse_output(out: str, line_number: int) -> str:
    for line in out.splitlines():
        search = "{}: note: Revealed type is ".format(line_number)
        if search in line:
            log(line)
            return "<b>{}</b>".format(line.split(search)[1].strip()[1:-1])

    try:
        log(line)  # no revealed type found
        return line.split("{}: ".format(line_number))[1]
    except Exception:
        return ""


def parse_locals_output(out: str, line_number: int) -> str:
    lines = []
    for line in out.splitlines():
        search = "{}: note: ".format(line_number)
        if search in line and "Revealed local types are:" not in line:
            lines.append(line.split(search)[1].strip())
        log(line)
    if len(lines) > 0:
        name_type_pairs = [line.split(": ") for line in lines]
        max_chars = max(len(pair[0]) for pair in name_type_pairs)
        lines = [
            "<b>{}</b> {}".format(
                pair[0].ljust(max_chars, "-").replace("-", "&nbsp;"), pair[1].replace("<", "&lt;").replace(">", "&gt;")
            )
            for pair in name_type_pairs
        ]
        return "<br>".join(lines)

    return "reveal_locals error"


class MypyRevealCommand(sublime_plugin.TextCommand):
    def run(self, edit, locals: bool = False, failed: bool = False) -> None:
        for r in self.view.sel():
            if locals:
                self.view.run_command("move_to", {"to": "eol"})
                self.view.run_command("insert", {"characters": "\nreveal_locals()"})
                contents = cast(str, self.view.substr(sublime.Region(0, self.view.size())))
                sublime.set_timeout_async(lambda: self.view.run_command("undo"), 0)
                self.run_mypy(contents=contents, line_number=self.view.rowcol(r.end())[0] + 2, locals=True)
            else:
                bounds = self.get_bounds(r)
                contents = cast(str, self.view.substr(sublime.Region(0, self.view.size())))
                selection = contents[bounds[0] : bounds[1]]

                if failed:
                    self.view.run_command("move_to", {"to": "eol"})
                    self.view.run_command("insert", {"characters": "\nreveal_type({})".format(selection)})
                    modified_contents = cast(str, self.view.substr(sublime.Region(0, self.view.size())))
                    sublime.set_timeout_async(lambda: self.view.run_command("undo"), 0)
                    self.run_mypy(
                        contents=modified_contents,
                        line_number=self.view.rowcol(bounds[0])[0] + 2,
                        selection=selection,
                        failed=True,
                    )
                else:
                    self.run_mypy(
                        contents=self.get_modified_contents(self.get_bounds(r), contents),
                        line_number=self.view.rowcol(bounds[0])[0] + 1,
                        selection=selection,
                    )
            break

    def show_popup(self, contents: str) -> None:
        def on_navigate(href: str) -> None:
            if href == "copy":
                sublime.set_clipboard(contents)
                sublime.active_window().status_message("MypyReveal: type info copied to clipboard")
                self.view.hide_popup()

        self.view.show_popup(
            "<style>body {{ min-height: 100px }}</style><p>{}</p><a href=\"copy\">Copy</a>".format(contents),
            max_width=800,
            on_navigate=on_navigate,
        )

    def get_modified_contents(self, bounds, contents):
        # type: (Tuple[int, int], str) -> str
        start, end = bounds
        return "{}reveal_type({}){}".format(contents[0:start], contents[start:end], contents[end:])

    def get_modified_contents_locals(self, begin: int, contents: str) -> str:
        return contents

    def get_bounds(self, region):
        # type: (Any) -> Tuple[int, int]
        start = region.begin()  # type: int
        end = region.end()  # type: int

        if start != end:
            return start, end

        # nothing is selected, so expand selection
        view_size = self.view.size()  # type: int
        included = list("{}{}_".format(string.ascii_letters, string.digits))

        # move selection backwards
        while start > 0:
            if cast(str, self.view.substr(start - 1)) not in included:
                break
            start -= 1

        # move selection forwards
        while end < view_size:
            if cast(str, self.view.substr(end)) not in included:
                break
            end += 1
        return start, end

    def run_mypy(
        self, contents: str, line_number: int, selection: str = "", locals: bool = False, failed: bool = False
    ) -> None:
        """Runs on another thread to avoid blocking main thread.
        """

        def sp() -> None:
            p = subprocess.Popen(
                [self.get_executable(), "-c", contents], cwd=self.project_path(), stdout=subprocess.PIPE
            )
            out, err = p.communicate()
            if locals:
                popup_contents = parse_locals_output(out.decode("utf-8"), line_number)  # type: str
                self.show_popup(popup_contents)
            else:
                if not failed and ": error: " in out.decode("utf-8"):  # retry on first failure
                    self.view.run_command("mypy_reveal", {"locals": False, "failed": True})
                    return
                popup_contents = parse_output(out.decode("utf-8"), line_number)
                if selection:
                    popup_contents = '<p>"{}"</p>{}'.format(selection, popup_contents)
                self.show_popup(popup_contents)

        threading.Thread(target=sp).start()

    def get_executable(self) -> str:
        project = self.view.window().project_data()
        try:
            return os.path.expanduser(project["settings"]["MypyReveal.executable"])
        except Exception:
            pass

        try:
            return os.path.expanduser(project["settings"]["SublimeLinter.linters.mypy.executable"])
        except Exception:
            pass

        try:
            return sublime.load_settings("MypyReveal.sublime-settings").get("executable", "mypy")
        except Exception:
            pass

        return "mypy"

    def project_path(self):
        # type: () -> Optional[str]
        project = self.view.window().project_data()
        if project is None:
            return None
        try:
            return os.path.expanduser(project["folders"][0]["path"])
        except Exception:
            return None
