#!/usr/bin/env python
import os
import sys
import webbrowser
from threading import Timer


def open_browser():
    webbrowser.open_new("http://127.0.0.1:8000/login/")


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce.settings")

    if "runserver" in sys.argv:
        Timer(1, open_browser).start()

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        raise
    execute_from_command_line(sys.argv)
