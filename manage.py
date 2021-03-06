#!/usr/bin/env python
import os
import sys

try:
    import pymysql

    pymysql.version_info = (1, 4, 6, "final", 0)  # change mysqlclient version
    pymysql.install_as_MySQLdb()
    print("running pymysql")

except ImportError:
    pass

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interpro.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
