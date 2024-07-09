-- Create a table that stores the corresponding dc_works.id
-- for every works.id with a dataset zenodo reference
CREATE TABLE rolap.zenodo_dataset_references AS
  SELECT work_references.work_id AS crossref_work_id, dc_works.id AS datacite_reference_id
  FROM work_references
  INNER JOIN dc_works ON dc_works.doi = work_references.doi
  WHERE dc_works.resource_type_general = 'Dataset';
