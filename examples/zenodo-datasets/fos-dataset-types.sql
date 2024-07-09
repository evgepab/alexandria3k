-- Create a report that shows the number of data sets referenced in each FoS class 
SELECT Count(*)
  FROM dc_work_subjects
  INNER JOIN rolap.zenodo_dataset_references zdr ON zdr.datacite_reference_id = work_id
  WHERE subject_scheme LIKE '%FOS%' 
  GROUP BY subject;