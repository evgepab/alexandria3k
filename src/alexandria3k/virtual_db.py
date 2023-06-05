#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022-2023  Diomidis Spinellis
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
"""Virtual database table access"""

# pylint: disable-next=import-error
import apsw


class TableMeta:
    """A container for table meta-data"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name, **kwargs):
        self.name = name

        # This table's key that refers to the parent table
        self.foreign_key = kwargs.get("foreign_key")

        # Parent table and its key that joins with this table's foreign key
        self.parent_name = kwargs.get("parent_name")
        self.primary_key = kwargs.get("primary_key")

        self.cursor_class = kwargs.get("cursor_class")
        self.extract_multiple = kwargs.get("extract_multiple")
        self.columns = kwargs["columns"]
        self.post_population_script = kwargs.get("post_population_script")

        self.delimiter = kwargs.get("delimiter") or ","

        # Create dictionary of columns by name
        self.columns_by_name = {}
        for column in self.columns:
            name = column.get_name()
            self.columns_by_name[name] = column

    def table_schema(self, prefix="", columns=None):
        """Return the SQL command to create a table's schema with the
        optional specified prefix.
        A columns array can be used to specify which columns to include."""
        if not columns or "*" in columns:
            columns = [f"  {c.get_definition()}" for c in self.columns]
        # A comma-separated list of the table's columns
        column_list = ",\n".join(columns)
        return f"CREATE TABLE {prefix}{self.name}(\n" + column_list + "\n);\n"

    def insert_statement(self):
        """Return an SQL command to insert data into the table"""
        # A comma-separated list of the table's columns
        columns = [c.get_name() for c in self.columns]
        column_list = ", ".join(columns)

        # A comma-separated list of one question mark per column
        values = ["?" for c in self.columns]
        values_list = ", ".join(values)

        return (
            f"INSERT INTO {self.name}({column_list}) VALUES ({values_list});"
        )

    def get_name(self):
        """Return the table's name"""
        return self.name

    def get_primary_key(self):
        """Return the parent table's column name that refers to our
        foreign key"""
        return self.primary_key

    def get_foreign_key(self):
        """Return our column that refers to the parent table's primary key"""
        return self.foreign_key

    def get_extract_multiple(self):
        """Return the function for obtaining multiple records"""
        return self.extract_multiple

    def get_post_population_script(self):
        """Return the SQL command to run after the table is populated"""
        return self.post_population_script

    def get_parent_name(self):
        """Return the name of the main table of which this has details"""
        return self.parent_name

    def get_cursor_class(self):
        """Return the table's specified cursor class"""
        return self.cursor_class

    def get_columns(self):
        """Return the table's columns"""
        return self.columns

    def get_value_extractor_by_ordinal(self, i):
        """Return defined value extraction function for column at ordinal i"""
        return self.columns[i].get_value_extractor()

    def get_value_extractor_by_name(self, name):
        """Return defined value extraction function for column name"""
        return self.columns_by_name[name].get_value_extractor()

    def get_column_definition_by_name(self, name):
        """Return defined column definition DDL for column name"""
        return self.columns_by_name[name].get_definition()


class ColumnMeta:
    """A container for column meta-data"""

    def __init__(self, name, value_extractor=None, **kwargs):
        self.name = name
        self.value_extractor = value_extractor
        self.description = kwargs.get("description")
        self.rowid = kwargs.get("rowid")

    def get_name(self):
        """Return column's name"""
        return self.name

    def get_definition(self):
        """Return column's DDL definition"""
        if self.rowid:
            # Special SQLite name and definition that makes rowid a
            # visible and stable row identifier.
            # See https://sqlite.org/forum/info/f78ca38d8d6bf67f
            return f"{self.name} INTEGER PRIMARY KEY"
        return self.name

    def get_description(self):
        """Return column's description, if any"""
        return self.description

    def get_value_extractor(self):
        """Return the column's value defined extraction function"""
        return self.value_extractor


# By convention column 1 of each table hold the container (file) id
# which is the index of the file in the files array
CONTAINER_ID_COLUMN = 1

ROWID_COLUMN = -1

CONTAINER_INDEX = 1
ROWID_INDEX = 2


class StreamingTable:
    """An apsw table streaming over data of the supplied table metadata"""

    def __init__(
        self, table_meta, table_dict, data_source, sample=lambda x: True
    ):
        """Not part of the apsw VTTable interface"""
        self.table_meta = table_meta
        self.table_dict = table_dict
        self.data_source = data_source
        self.sampling_function = sample

    def BestIndex(self, _constraints, _orderbys):
        """Called by the Engine to determine the best available index
        for the operation at hand"""
        return None

    def Disconnect(self):
        """Called when a reference to a virtual table is no longer used"""

    Destroy = Disconnect

    def sample(self, data_id):
        """Return true if the identified data element should be included
        in the sample given in the table's constructor."""
        return self.sampling_function(data_id)

    def get_table_meta_by_name(self, name):
        """Return the metadata of the specified table"""
        return self.table_dict[name]

    def get_table_meta(self):
        """Return the metadata of this table"""
        return self.table_meta

    def get_data_source(self):
        """Return the data source of this table"""
        return self.data_source

    def cursor(self, table_meta):
        """Return the cursor associated with this table.  The constructor
        for cursors embedded in others takes a parent cursor argument.  To
        handle this requirement, this method recursively calls itself until
        it reaches the top-level table."""
        cursor_class = table_meta.get_cursor_class()
        parent_name = table_meta.get_parent_name()
        if not parent_name:
            return cursor_class(self)
        parent = self.get_table_meta_by_name(parent_name)
        return cursor_class(self, self.cursor(parent))

    def Open(self):
        """Return the table's cursor object"""
        return self.cursor(self.table_meta)

    def get_value_extractor_by_ordinal(self, column_ordinal):
        """Return the value extraction function for column at specified
        ordinal.  Not part of the apsw interface."""
        return self.table_meta.get_value_extractor_by_ordinal(column_ordinal)


class StreamingCachedContainerTable(StreamingTable):
    """An apsw table streaming over data of the supplied table metadata.
    This works over a cached data container (e.g. a parsed JSON or XML
    file) that allows indexing entries within it."""

    # pylint: disable-next=arguments-differ
    def BestIndex(self, constraints, _orderbys):
        """Called by the Engine to determine the best available index
        for the operation at hand"""
        # print(f"BestIndex gets c={constraints} o={_orderbys}")
        used_constraints = []
        index_number = 0
        for column, operation in constraints:
            if (
                column == CONTAINER_ID_COLUMN
                and operation == apsw.SQLITE_INDEX_CONSTRAINT_EQ
            ):
                # Pass value to Filter as constraint_arg[0], and do not
                # require the engine to perform extra checks (exact match)
                used_constraints.append((0, False))
                index_number |= CONTAINER_INDEX
            elif (
                column == ROWID_COLUMN
                and operation == apsw.SQLITE_INDEX_CONSTRAINT_EQ
            ):
                # Pass value to Filter as constraint_arg[1], and do not
                # require the engine to perform extra checks (exact match)
                used_constraints.append((1, False))
                index_number |= ROWID_INDEX
            else:
                # No suitable index
                used_constraints.append(None)
        if index_number != 0:
            # print(f"BestIndex returns: {index_number}, {used_constraints}")
            return (
                used_constraints,
                # First argument to Filter: 0 no index, 1 file index,
                # 2 rowid index, 3 both indexes
                index_number,
                None,  # index name (second argument to Filter)
                False,  # results are not in orderbys order
                2000
                / index_number,  # about 2000 disk i/o (8M file / 4k block)
            )
        return None
