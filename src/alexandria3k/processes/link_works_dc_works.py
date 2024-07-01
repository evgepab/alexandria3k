#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2023-2024  Evgenia Pampidi
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Link Crossref works with the corresponding DataCite works"""

import sqlite3

from alexandria3k.common import (
    ensure_table_exists,
    get_string_resource,
)
from alexandria3k import perf
from alexandria3k.db_schema import ColumnMeta, TableMeta


tables = [
    TableMeta(
        "works_dc_works",
        columns=[
            ColumnMeta("crossref_work_id"),
            ColumnMeta("datacite_work_id"),
        ],
    )
]


def process(database_path):
    """
    Create a one to one table linking Crossref works with the
    corresponding DataCite works.

    :param database_path: The path specifying the SQLite database
        to process and populate.
        The database shall already contain the Datacite dataset and the
        Crossref `work_subjects` table.
    :type database_path: str
    """
    connection = sqlite3.connect(database_path)
    ensure_table_exists(connection, "works")
    ensure_table_exists(connection, "dc_works")
    script = get_string_resource("sql/link-works-dc-works.sql")
    cursor = connection.cursor()
    cursor.executescript(script)
    perf.log("link_works_dc_works")
