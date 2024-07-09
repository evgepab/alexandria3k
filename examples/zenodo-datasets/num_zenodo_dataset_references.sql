-- Create a table with the number of each work's zenodo dataset references
CREATE TABLE rolap.num_zenodo_dataset_references AS
  SELECT crossref_work_id, Count(*) AS num_dataset_references
  FROM rolap.zenodo_dataset_references
  GROUP BY crossref_work_id;