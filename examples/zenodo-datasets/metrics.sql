-- Output metrics of a fully-populated Zenodo database

SELECT "works" AS type,
  (SELECT Count(*) FROM dc_works) AS records UNION
SELECT "datasets" AS type,
  (SELECT Count(*) FROM dc_works WHERE resource_type_general = 'Dataset') AS records UNION
SELECT "cited_datasets" AS type,
  (SELECT Count(Distinct(datacite_reference_id)) FROM rolap.zenodo_dataset_references) AS records UNION
SELECT "works_citations" AS type,
  (SELECT Count(doi) FROM work_references WHERE doi like '%zenodo%') AS records UNION
SELECT "unique_work_citations" AS type,
  (SELECT Count(Distinct(work_id)) FROM work_references) AS records UNION
SELECT "datasets_citations" AS type,
  (SELECT Count(*) FROM rolap.zenodo_dataset_references) AS records UNION
SELECT "unique_dataset_citations" AS type,
  (SELECT Count(Distinct(crossref_work_id)) FROM rolap.zenodo_dataset_references) AS records UNION
SELECT "independent_dataset_citations" AS type,
  (SELECT Sum(indepedent_citations) FROM rolap.dataset_reusability) AS records;
