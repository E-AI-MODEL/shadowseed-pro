"""PyInstaller hook for Gradio's runtime source introspection.

Gradio's component metaclass reads module source files from paths derived from
``__file__`` while constructing component stubs. Pure Python modules are
normally stored in PyInstaller's PYZ archive, so those source paths do not exist
as ordinary files in a frozen app. Collect Gradio's Python sources as data in
addition to the normal frozen modules so that runtime introspection sees the
same package-relative paths.
"""

from PyInstaller.utils.hooks import collect_data_files


datas = collect_data_files("gradio", include_py_files=True)
