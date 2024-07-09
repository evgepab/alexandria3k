-- Create a report that shows the total number of independent citations by year
SELECT published_year, sum(reuse_status)
  FROM rolap.reference_reusability rr 
  INNER JOIN works ON works.id = rr.crossref_work_id 
  GROUP BY works.published_year
  ORDER BY published_year;