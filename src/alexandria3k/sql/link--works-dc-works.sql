/*
 * Alexandria3k Crossref bibliographic metadata processing
 * Copyright (C) 2023-2024 Evgenia Pampidi
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * Normalize work subjects by linking them with ASJCs
 */

DROP TABLE IF EXISTS works_dc_works;

CREATE TABLE works_dc_works AS
  SELECT works.id AS crossref_work_id, dc_works.id AS datacite_work_id
    FROM works
    INNER JOIN dc_works ON dc_works.doi = works.doi;
