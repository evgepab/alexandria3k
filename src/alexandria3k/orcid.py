#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022  Diomidis Spinellis
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
"""Populate ORCID data tables"""

import abc
import os
import tarfile
import xml.etree.ElementTree as ET

import apsw

from virtual_db import ColumnMeta, TableMeta, CONTAINER_ID_COLUMN, FilesCursor

# The ORCID XML namespaces in XPath format
ACTIVITIES = "{http://www.orcid.org/ns/activities}"
ADDRESS = "{http://www.orcid.org/ns/address}"
BULK = "{http://www.orcid.org/ns/bulk}"
COMMON = "{http://www.orcid.org/ns/common}"
DEPRECATED = "{http://www.orcid.org/ns/deprecated}"
DISTINCTION = "{http://www.orcid.org/ns/distinction}"
EDUCATION = "{http://www.orcid.org/ns/education}"
EMAIL = "{http://www.orcid.org/ns/email}"
EMPLOYMENT = "{http://www.orcid.org/ns/employment}"
ERROR = "{http://www.orcid.org/ns/error}"
EXTERNAL_IDENTIFIER = "{http://www.orcid.org/ns/external-identifier}"
FUNDING = "{http://www.orcid.org/ns/funding}"
HISTORY = "{http://www.orcid.org/ns/history}"
INTERNAL = "{http://www.orcid.org/ns/internal}"
INVITED_POSITION = "{http://www.orcid.org/ns/invited-position}"
KEYWORD = "{http://www.orcid.org/ns/keyword}"
MEMBERSHIP = "{http://www.orcid.org/ns/membership}"
OTHER_NAME = "{http://www.orcid.org/ns/other-name}"
PEER_REVIEW = "{http://www.orcid.org/ns/peer-review}"
PERSON = "{http://www.orcid.org/ns/person}"
PERSONAL_DETAILS = "{http://www.orcid.org/ns/personal-details}"
PREFERENCES = "{http://www.orcid.org/ns/preferences}"
QUALIFICATION = "{http://www.orcid.org/ns/qualification}"
RECORD = "{http://www.orcid.org/ns/record}"
RESEARCHER_URL = "{http://www.orcid.org/ns/researcher-url}"
RESEARCH_RESOURCE = "{http://www.orcid.org/ns/research-resource}"
SERVICE = "{http://www.orcid.org/ns/service}"
WORK = "{http://www.orcid.org/ns/work}"


def get_element(tree, path):
    """Return the text value of the specified element path of the given
    tree."""
    element = tree.find(path)
    if element is None:
        return None
    return element.text


def getter(path):
    """Return a function to return an element with the specified
    path from a given tree."""
    return lambda tree: get_element(tree, path)


# Map from XML to relational schema
# The XML schema is described in
# https://info.orcid.org/documentation/integration-guide/orcid-record/#Research_Resources
# https://github.com/ORCID/orcid-model/blob/master/src/main/resources/record_3.0/README.md

START_END_DATE = [
    ColumnMeta("start_year", getter(f"{COMMON}start-date/{COMMON}year")),
    ColumnMeta("start_month", getter(f"{COMMON}start-date/{COMMON}month")),
    ColumnMeta("start_day", getter(f"{COMMON}start-date/{COMMON}day")),
    ColumnMeta("end_year", getter(f"{COMMON}end-date/{COMMON}year")),
    ColumnMeta("end_month", getter(f"{COMMON}end-date/{COMMON}month")),
    ColumnMeta("end_day", getter(f"{COMMON}end-date/{COMMON}day")),
]

ORGANIZATION = [
    ColumnMeta(
        "organization_name", getter(f"{COMMON}organization/{COMMON}name")
    ),
    ColumnMeta(
        "organization_city",
        getter(f"{COMMON}organization/{COMMON}address/{COMMON}city"),
    ),
    ColumnMeta(
        "organization_region",
        getter(f"{COMMON}organization/{COMMON}address/{COMMON}region"),
    ),
    ColumnMeta(
        "organization_country",
        getter(f"{COMMON}organization/{COMMON}address/{COMMON}country"),
    ),
    ColumnMeta(
        "organization_identifier",
        getter(
            f"{COMMON}organization/{COMMON}disambiguated-organization/{COMMON}disambiguated-organization-identifier"
        ),
    ),
]

DEPARTMENT_NAME_ROLE = [
    ColumnMeta("department_name", getter(f"{COMMON}department-name")),
    ColumnMeta("role_title", getter(f"{COMMON}role-title")),
]

AFFILIATION = ORGANIZATION + DEPARTMENT_NAME_ROLE + START_END_DATE

tables = [
    TableMeta(
        "persons",
        columns=[
            ColumnMeta(
                "orcid", getter(f"{COMMON}orcid-identifier/{COMMON}path")
            ),
            ColumnMeta(
                "given_names",
                getter(
                    f"{PERSON}person/{PERSON}name/{PERSONAL_DETAILS}given-names"
                ),
            ),
            ColumnMeta(
                "family_name",
                getter(
                    f"{PERSON}person/{PERSON}name/{PERSONAL_DETAILS}family-name"
                ),
            ),
            ColumnMeta(
                "biography",
                getter(
                    f"{PERSON}person/{PERSON}biography/{PERSONAL_DETAILS}content"
                ),
            ),
        ],
    ),
    TableMeta(
        "researcher_urls",
        records_path=f"{PERSON}person/{RESEARCHER_URL}researcher-urls/{RESEARCHER_URL}researcher-url",
        columns=[
            ColumnMeta("orcid"),
            ColumnMeta("name", getter(f"{RESEARCHER_URL}url-name")),
            ColumnMeta("url", getter(f"{RESEARCHER_URL}url")),
        ],
    ),
    TableMeta(
        "person_countries",
        records_path=f"{PERSON}person/{ADDRESS}addresses/{ADDRESS}address",
        columns=[
            ColumnMeta("orcid"),
            ColumnMeta("country", getter(f"{ADDRESS}country")),
        ],
    ),
    TableMeta(
        "person_keywords",
        records_path=f"{PERSON}person/{KEYWORD}keywords/{KEYWORD}keyword",
        columns=[
            ColumnMeta("orcid"),
            ColumnMeta("keyword", getter(f"{KEYWORD}content")),
        ],
    ),
    TableMeta(
        "person_external_identifiers",
        records_path=f"{PERSON}person/{EXTERNAL_IDENTIFIER}external-identifiers/{EXTERNAL_IDENTIFIER}external-identifier",
        columns=[
            ColumnMeta("orcid"),
            ColumnMeta("type", getter(f"{COMMON}external-id-type")),
            ColumnMeta("value", getter(f"{COMMON}external-id-value")),
            ColumnMeta("url", getter(f"{COMMON}external-id-url")),
        ],
    ),
    TableMeta(
        "distinctions",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}distinctions/{ACTIVITIES}affiliation-group/{DISTINCTION}distinction-summary",
        columns=[
            ColumnMeta("orcid"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "educations",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}educations/{ACTIVITIES}affiliation-group/{EDUCATION}education-summary",
        columns=[
            ColumnMeta("orcid"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "employments",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}employments/{ACTIVITIES}affiliation-group/{EMPLOYMENT}employment-summary",
        columns=[
            ColumnMeta("orcid"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "invited_positions",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}invited-positions/{ACTIVITIES}affiliation-group/{INVITED_POSITION}invited-position-summary",
        columns=[
            ColumnMeta("orcid"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "memberships",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}memberships/{ACTIVITIES}affiliation-group/{MEMBERSHIP}membership-summary",
        columns=[
            ColumnMeta("orcid"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "qualifications",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}qualifications/{ACTIVITIES}affiliation-group/{QUALIFICATION}qualification-summary",
        columns=[
            ColumnMeta("orcid"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "services",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}services/{ACTIVITIES}affiliation-group/{SERVICE}service-summary",
        columns=[
            ColumnMeta("orcid"),
        ]
        + AFFILIATION,
    ),
    TableMeta(
        "fundings",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}fundings/{ACTIVITIES}group/{FUNDING}funding-summary",
        # TODO external-ids, contributors
        columns=[
            ColumnMeta("orcid"),
            ColumnMeta("title", getter(f"{FUNDING}funding-title")),
            ColumnMeta("type", getter(f"{FUNDING}funding-type")),
            ColumnMeta(
                "short_description", getter(f"{COMMON}short-description")
            ),
            ColumnMeta("amount", getter(f"{COMMON}amount")),
            ColumnMeta("url", getter(f"{COMMON}url")),
        ]
        + START_END_DATE
        + ORGANIZATION,
    ),
    TableMeta(
        "peer_reviews",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}peer-reviews/{ACTIVITIES}group/{ACTIVITIES}peer-review-group/{PEER_REVIEW}peer-review-summary",
        columns=[
            ColumnMeta("orcid"),
            ColumnMeta("reviewer_role", getter(f"{PEER_REVIEW}reviewer-role")),
            ColumnMeta("review_type", getter(f"{PEER_REVIEW}review-type")),
            ColumnMeta("subject_type", getter(f"{PEER_REVIEW}subject-type")),
            ColumnMeta("subject_name", getter(f"{PEER_REVIEW}subject-name")),
            ColumnMeta("subject_url", getter(f"{PEER_REVIEW}subject-url")),
            ColumnMeta("group_id", getter(f"{PEER_REVIEW}review-group-id")),
            ColumnMeta(
                "completion_year",
                getter(f"{PEER_REVIEW}completion-date/{COMMON}year"),
            ),
            ColumnMeta(
                "completion_month",
                getter(f"{PEER_REVIEW}completion-date/{COMMON}month"),
            ),
            ColumnMeta(
                "completion_day",
                getter(f"{PEER_REVIEW}completion-date/{COMMON}day"),
            ),
            ColumnMeta(
                "organization_name",
                getter(f"{PEER_REVIEW}convening-organization/{COMMON}name"),
            ),
            ColumnMeta(
                "organization_city",
                getter(
                    f"{PEER_REVIEW}convening-organization/{COMMON}address/{COMMON}city"
                ),
            ),
            ColumnMeta(
                "organization_region",
                getter(
                    f"{PEER_REVIEW}convening-organization/{COMMON}address/{COMMON}region"
                ),
            ),
            ColumnMeta(
                "organization_country",
                getter(
                    f"{PEER_REVIEW}convening-organization/{COMMON}address/{COMMON}country"
                ),
            ),
        ],
    ),
    TableMeta(
        "research_resources",
        records_path=f"{ACTIVITIES}activities-summary/{ACTIVITIES}research-resources/{ACTIVITIES}group/{RESEARCH_RESOURCE}research-resource-summary",
        columns=[
            ColumnMeta("orcid"),
            ColumnMeta(
                "title",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{RESEARCH_RESOURCE}title/{COMMON}title"
                ),
            ),
            ColumnMeta(
                "start_year",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}start-date/{COMMON}year"
                ),
            ),
            ColumnMeta(
                "start_month",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}start-date/{COMMON}month"
                ),
            ),
            ColumnMeta(
                "start_day",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}start-date/{COMMON}day"
                ),
            ),
            ColumnMeta(
                "end_year",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}end-date/{COMMON}year"
                ),
            ),
            ColumnMeta(
                "end_month",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}end-date/{COMMON}month"
                ),
            ),
            ColumnMeta(
                "end_day",
                getter(
                    f"{RESEARCH_RESOURCE}proposal/{COMMON}end-date/{COMMON}day"
                ),
            ),
        ],
    ),
]

table_dict = {t.get_name(): t for t in tables}


def get_table_meta_by_name(name):
    """Return the metadata of the specified table"""
    return table_dict[name]


class TableFiller:
    """An object for adding records to a table"""

    def __init__(self, database, table_name, column_names):
        # One cursor per object to allow caching the SQL statement
        self.cursor = database.cursor()

        # {title, isbn, rating} → ":title, :isbn, :rating"
        values = ",".join(map(lambda n: f":{n}", column_names))
        self.statement = f"INSERT INTO {table_name} VALUES({values})"

        # Create a dictionary of functions to extract the record values for
        # the specified columns
        self.extractors = {}
        table = get_table_meta_by_name(table_name)
        self.records_path = table.get_records_path()
        for cname in column_names:
            self.extractors[cname] = table.get_value_extractor_by_name(cname)

    def add_records(self, element_tree, orcid):
        """Add to the table the required values from the XML element tree"""
        if self.records_path:
            self.add_multiple_records(element_tree, orcid)
        else:
            self.add_single_record(element_tree, orcid)

    def add_single_record(self, element_tree, orcid):
        """Add to the table the required values from the XML element tree"""
        # Create dictionary of names/values to insert
        values = {}
        not_null_values = 0
        for (column_name, extractor) in self.extractors.items():
            if column_name == "orcid":
                values[column_name] = orcid
            else:
                value = extractor(element_tree)
                values[column_name] = value
                if value is not None:
                    not_null_values += 1

        # No insertion if all non-key values are NULL
        if not_null_values == 0:
            return

        self.cursor.execute(
            self.statement,
            values,
            prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
        )

    def add_multiple_records(self, element_tree, orcid):
        """Add to the table the required values from the XML element tree"""
        records = []
        for record in element_tree.findall(self.records_path):
            # Create dictionary of names/values to insert
            values = {}
            not_null_values = 0
            for (column_name, extractor) in self.extractors.items():
                if column_name == "orcid":
                    values[column_name] = orcid
                else:
                    value = extractor(record)
                    values[column_name] = value
                    if value is not None:
                        not_null_values += 1

            # No insertion if all non-key values are NULL
            if not_null_values > 0:
                records.append(values)

        self.cursor.executemany(
            self.statement,
            records,
            prepare_flags=apsw.SQLITE_PREPARE_PERSISTENT,
        )


def populate(data_path, database_path, columns, authors_only):
    """Populate the specified SQLite database.
    The database is created if it does not exist.
    If it exists, the populated tables are dropped
    (if they exist) and recreated anew as specified.

    columns is an array containing strings of
    table_name.column_name or table_name.*
    """

    population_columns = {}

    def add_column(table, column):
        """Add a column required for executing a query to the
        specified dictionary"""
        if column == "*":
            columns = get_table_meta_by_name(table).get_columns()
            column_names = map(lambda c: c.get_name(), columns)
            population_columns[table] = set(column_names)
        elif table in population_columns:
            population_columns[table].add(column)
        else:
            population_columns[table] = {column}

    # By default include all tables and columns
    if not columns:
        columns = []
        for table in tables:
            columns.append(f"{table.get_name()}.*")

    # A dictionary of columns to be populated for each table
    for col in columns:
        (table, column) = col.split(".")
        if not table or not column:
            fail(f"Invalid column specification: {col}")
        add_column(table, column)

    # Create empty tables and their TableFiller objects
    db = apsw.Connection(database_path)
    cursor = db.cursor()
    table_fillers = []
    for (table_name, table_columns) in population_columns.items():
        # Table creation
        table = get_table_meta_by_name(table_name)
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(table.table_schema("", table_columns))

        # Value addition
        table_fillers.append(TableFiller(db, table_name, table_columns))

    # Streaming read from compressed file
    with tarfile.open(data_path, "r|gz") as tar:
        for tar_info in tar:
            if not tar_info.isreg():
                continue

            # Obtain ORCID from file name to avoid extraction and parsing
            (_root, _checksum, file_name) = tar_info.name.split("/")
            orcid = file_name[:-4]

            # Skip records of non-linked authors
            if authors_only:
                cursor.execute(
                    "SELECT DISTINCT 1 FROM work_authors WHERE orcid = ?",
                    (orcid,),
                )
                if not cursor.fetchone():
                    continue

            # Extract and parse XML data
            reader = tar.extractfile(tar_info)
            data = reader.read()
            element_tree = ET.fromstring(data)
            orcid_xml = element_tree.find(
                f"{COMMON}orcid-identifier/{COMMON}path"
            )
            # Skip error records
            if orcid_xml is None:
                continue

            assert orcid == orcid_xml.text

            # Insert data to the specified tables
            for filler in table_fillers:
                filler.add_records(element_tree, orcid)

    for table_name in population_columns.keys():
        cursor.execute(
            f"CREATE INDEX {table_name}_orcid_idx ON {table_name}(orcid)"
        )