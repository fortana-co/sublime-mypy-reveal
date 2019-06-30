# MypyReveal

A [Sublime Text](http://www.sublimetext.com/) plugin that uses [mypy](https://mypy.readthedocs.io/en/stable/) to reveal the type of the variable under your cursor, or to reveal the types of all local variables, using `reveal_type` or `reveal_locals`. [Read more here](https://mypy.readthedocs.io/en/latest/cheat_sheet_py3.html#when-you-re-puzzled-or-when-things-are-complicated).

## Requirements

Make sure you install **mypy 0.711** or later first, and that it's in your `$PATH`.

## Installation

Search for **MypyReveal** in Package Control.

## Usage

Search for **MypyReveal** in the command palette, and run either **MypyReveal: Type** or **MypyReveal: Locals**.

### Key Bindings

If you wanted to bind <kbd>ctrl+t</kbd> to reveal type and <kbd>alt+t</kbd> to reveal locals, you would insert the following into your `.sublime-keymap`:

```json
{
  "keys": ["ctrl+t"],
  "command": "mypy_reveal",
  "context": [{ "key": "selector", "operator": "equal", "operand": "source.python" }]
},
{
  "keys": ["alt+t"],
  "command": "mypy_reveal",
  "args": {
    "locals": true
  },
  "context": [{ "key": "selector", "operator": "equal", "operand": "source.python" }]
},
```

### Custom Executable

Like Sublime Linter, this plugin assumes `mypy` is in the `$PATH` available to Sublime Text. If it's not, you'll have to set your own `executable` path in settings.

If you want per-project `executable` paths, e.g. because you want mypy to have access to the packages you have installed in a virtual env, add the following to your project settings:

```json
{
  "folders": [
    {
      "path": "..."
    }
  ],
  "settings": {
    "MypyReveal.executable": "/path/to/mypy"
  }
}
```

This plugin is designed to work in conjunction with the [mypy Sublime Linter plugin](https://github.com/fredcallaway/SublimeLinter-contrib-mypy).

If, in your project settings, you set `SublimeLinter.linters.mypy.executable` instead of `MypyReveal.executable`, MypyReveal will fall back to this setting.
