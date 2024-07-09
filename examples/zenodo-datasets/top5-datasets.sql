-- Display some general information regarding the top 5
-- most cited data sets with independent citations
SELECT datacite_reference_id, doi, title, publication_year, Count(indepedent_citations) citations
  FROM rolap.dataset_reusability dr
  INNER JOIN dc_works ON dr.datacite_reference_id = dc_works.id
  INNER JOIN dc_work_titles ON dr.datacite_reference_id = dc_work_titles.work_id
  GROUP BY datacite_reference_id
  ORDER BY citations DESC
  LIMIT 5;