-- Create table that shows the reuse status for each data set reference
CREATE TABLE rolap.reference_reusability AS
  SELECT 
    crossref_work_id, 
    datacite_reference_id,
    CASE 
      WHEN EXISTS (
        SELECT 1
          FROM (
            SELECT work_id, family || ', ' || given AS name
              FROM work_authors
          ) wan
          INNER JOIN dc_work_creators dcwc
          ON wan.name = dcwc.name
          WHERE wan.work_id = zdr.crossref_work_id
          AND dcwc.work_id = zdr.datacite_reference_id
      )
      THEN 0 -- cited by one of the authors
      ELSE 1
    END AS reuse_status
  FROM rolap.zenodo_dataset_references AS zdr
