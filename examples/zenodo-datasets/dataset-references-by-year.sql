-- Create a report with total number of zenoodo references per year
SELECT published_year AS year, Sum(num_dataset_references) AS sum_dataset_references
  FROM rolap.num_zenodo_dataset_references nzdr
  INNER JOIN works ON nzdr.crossref_work_id = works.id
  GROUP BY year
  ORDER BY year;