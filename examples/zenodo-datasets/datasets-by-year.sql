-- Create a report with total number of Zenodo data sets publications per year
SELECT publication_year as year, Count(*) as total_datasets
  FROM dc_works
  WHERE resource_type_general = 'Dataset'
  GROUP BY year
  ORDER BY year;