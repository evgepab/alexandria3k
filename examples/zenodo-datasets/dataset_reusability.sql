-- Create table that shows for each dataset how many indepedent and total citations it has
CREATE TABLE rolap.dataset_reusability AS
  SELECT datacite_reference_id, Sum(reuse_status) AS indepedent_citations, Count(*) AS citations
    FROM rolap.reference_reusability
    GROUP BY datacite_reference_id;
