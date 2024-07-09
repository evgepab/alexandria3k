#
# Analyze Zenodo's publications research
#

export MAINDB?=zenodo
export DEPENDENCIES=populate zenodo

include ../common/Makefile

# Populate database with Crossref publications with Zenodo references
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --debug progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --columns works.id \
	    works.published_year \
		work_references.work_id \
	    work_references.doi \
	    work_authors.work_id \
	    work_authors.family \
	    work_authors.given \
	  --row-selection "work_references.doi like '%zenodo%'"
	touch $@

# Populate database with Zenodo publications
zenodo: $(DATACITE)
	$(TIME) $(A3K) --debug progress \
	  populate "$(MAINDB).db" datacite $(DATACITE) \
	  --row-selection "dc_works.doi like '%zenodo%' AND dc_works.publication_year BETWEEN 2014 AND 2023"