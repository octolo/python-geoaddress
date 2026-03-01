#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def create_superuser():
    """Creates default superuser if none exists."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("📦 Creating superuser: admin/admin")
        User.objects.create_superuser("admin", "admin@example.com", "admin")
        print("✅ Superuser created successfully!")
        print("   Username: admin")
        print("   Password: admin")
    else:
        print("✅ Superuser already exists")


def main():
    """Runs administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        execute_from_command_line(sys.argv)
        create_superuser()
        return

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
