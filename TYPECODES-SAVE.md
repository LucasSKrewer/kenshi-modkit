# Typecodes de runtime (saves)

Gerado por `python typecodes_save.py`. Estes typecodes **não** aparecem em `data/` e **não** estão no `fcs.def`: são o que o jogo cria em partida. Os nomes aqui são **inferidos** do que cada registro referencia, de em que arquivo ele mora e de como se chama — não são autoridade do jogo.

| typecode | o que é (inferido) | registros | onde mora | exemplos de nome | campos típicos |
|---|---|---|---|---|---|
| 34 | **esquadrão vivo** | 18031 | `.save` | Saqueadores Sangrentos_9; Saqueadores Sangrentos_1 | `intact`, `is resident`, `special`, `dead` |
| 35 | **objeto colocado no mundo (prédio/mobília)** | 17580 | `.zone` | 0 | `foliage`, `pause`, `is public day`, `is complete` |
| 42 | **não identificado** | 12788 | `.zone`, `.platoon` | 0 | `death`, `in inventory`, `charges`, `quality` |
| 94 | **estado de cidade + estoque das lojas** | 4300 | `.save` | Town state RT; Town state Laboratório Ala | `trade goods (ref)`, `handCS`, `handS`, `handI` |
| 83 | **não identificado** | 4254 | `.zone` | 0 | `is inside building`, `respawn time`, `isInsideBuildingCS`, `isInsideBuildingS` |
| 41 | **não identificado** | 1973 | `.zone`, `.platoon` | 0 |  |
| 4 | **ITEM** | 1734 | `.zone` | 0 | `death`, `in inventory`, `charges`, `quality` |
| 9 | **controle de facção em runtime** | 1315 | `.save` | 0 | `updatetime`, `num plats`, `num poss`, `num requests` |
| 37 | **estado de facção** | 1315 | `.save` | Guilda dos Médicos; Ninjas do Despojo | `prosperity`, `platoonIDs`, `gamedata stringID`, `trust204` |
| 39 | **não identificado** | 1106 | `.save` | 0 | `BCS`, `BS`, `BI`, `BC` |
| 57 | **não identificado** | 581 | `.platoon` | 0 | `coma`, `dead`, `unconcious`, `incapacitated` |
| 25 | **STATS** | 581 | `.platoon` | Servo da Tempestade; Tertius Knight Commander | `free attribute points`, `xp`, `unarmed`, `bow` |
| 66 | **dados de raça do personagem** | 581 | `.platoon` | 0 | `Age`, `sex female`, `in editor`, `Waist` |
| 67 | **não identificado** | 581 | `.platoon` | ai | `jobs`, `pjobT0CS`, `pjobT0S`, `pjobT0C` |
| 36 | **não identificado** | 581 | `.platoon` | 0 | `shaved`, `tn`, `escap`, `kidn` |
| 30 | **não identificado** | 24 | `.save`, `.zone`, `.platoon` | 0 | `char count` |
| 40 | **não identificado** | 6 | `.save` | 0 | `R616S`, `R616I`, `R616C`, `616I` |
| 28 | **não identificado** | 6 | `.save` | 0 | `70_w_wi_bu_s_e`, `70_w_wi_bu_s_s`, `70_w_wi_bu_a_e`, `69_w_wi_str` |
| 21 | **não identificado** | 6 | `.save` | 0 | `num finished`, `num currents`, `paid120`, `paid119` |
| 108 | **não identificado** | 6 | `.save` | 0 | `total` |
| 56 | **não identificado** | 6 | `.save` | 0 | `zones (ref)`, `mods (ref)`, `usedUniquesPlayer106`, `usedUniquesPlayer102` |
| 38 | **não identificado** | 6 | `.save` | 0 |  |

## Por que cada rótulo

- **4 — ITEM**: mesmo typecode das definições: instância de item no mundo.
- **9 — controle de facção em runtime**: campos `num plats`, `num poss`, `num requests`, `num actives`, `fwc id`, `faction`.
- **25 — STATS**: mesmo typecode das definições: stats em runtime.
- **34 — esquadrão vivo**: nomes `<Facção>_<n>`; campos `intact`, `dead`, `imprisoned`, `squad index`, `hometownCS`.
- **35 — objeto colocado no mundo (prédio/mobília)**: campos `foliage`, `is inside building`, `destroyed`, `world Y pos`; só em `.zone`.
- **37 — estado de facção**: aponta para FACTION; um por facção.
- **66 — dados de raça do personagem**: um por `.platoon`, aponta para RACE.
- **94 — estado de cidade + estoque das lojas**: nomes literais `Town state <cidade>`; 175 mil refs `trade goods` apontando para ITEM.

## Como os registros de save se ligam

Diferente dos mods, um registro de save **não** referencia outro pelo `strid`: usa **handles numéricos** (`handC`, `handS`, `handI`, `handCS`, mais `handTYPE`). É por isso que a coluna de referências fica quase toda vazia aqui, e é o que liga esses registros aos pools de id da cauda do arquivo (ver FORMATO.md).
