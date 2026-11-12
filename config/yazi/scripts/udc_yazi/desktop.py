import os
import subprocess
from .settings import desktop_env


def open_default(paths):
    for path in paths:
        subprocess.run(["xdg-open", path], env=desktop_env(), check=True)


def choose(paths):
    # Import GTK only for the chooser; terminal/editor actions do not depend on it.
    clean = desktop_env()
    for key in ("GBM_BACKENDS_PATH", "LIBGL_DRIVERS_PATH", "__EGL_VENDOR_LIBRARY_FILENAMES"):
        if key not in clean:
            os.environ.pop(key, None)
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gio, Gtk
    if not Gtk.init_check()[0]:
        raise RuntimeError("打开方式窗口需要可用的图形会话")
    files = [Gio.File.new_for_path(path) for path in paths]
    types = [f.query_info("standard::content-type", Gio.FileQueryInfoFlags.NONE, None)
             .get_content_type() for f in files]
    if len(set(types)) != 1:
        raise ValueError("请一次选择相同类型的文件；不同类型请分别选择打开方式")
    dialog = Gtk.AppChooserDialog(content_type=types[0])
    dialog.set_title("打开方式")
    dialog.set_heading("选择用于打开此文件的应用" if len(files) == 1 else f"选择用于打开 {len(files)} 个文件的应用")
    chooser = dialog.get_widget()
    chooser.set_show_all(True)
    try:
        if dialog.run() != Gtk.ResponseType.OK:
            return
        app = dialog.get_app_info()
        if app is None:
            return
        # launch() does not change the default MIME association.
        app.launch(files, dialog.get_display().get_app_launch_context())
    finally:
        dialog.destroy()
