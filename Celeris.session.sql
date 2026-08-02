SELECT
    p.id,
    p.grupo_id,
    g.name AS nm_papel,
    p.ds_descricao,
    p.sn_ativo
FROM papel p
JOIN auth_group g ON g.id = p.grupo_id;