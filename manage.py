#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velican2.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    from django.conf import settings
    settings.SUBCOMMAND = sys.argv[1] if len(sys.argv) > 1 else "help"
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
