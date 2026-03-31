BEGIN;

-- nom de schéma définitif
SET search_path TO psch;



--tables à supp : tables temporaires

DROP TABLE if exists
    tmp_cnc, 
    tmp_etab_cine, 
    tmp_programation, 
    tmp_rsa, 
    raw_wikidata1, 
    raw_wikidata2, 
    tmp_titre,
    tmp_wiki1,
	tmp_wiki2,
    raw_cnc,
    raw_etab_cine,
    raw_prog,
    raw_rsa
CASCADE;

commit ;
