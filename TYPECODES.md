# Mapa de typecodes

Gerado por `python typecodes.py`. Dois métodos independentes:

1. **campos** — casa o conjunto de campos dos registros de `data/` com as seções do `fcs.def`. `recall` é a fração dos campos vistos que o tipo explica.
2. **referências** — o `fcs.def` diz qual tipo cada campo de referência aponta (`clothing: ARMOUR`); seguindo as refs reais até o typecode do registro apontado, o tipo sai sem depender do método 1.

`CONFIRMADO` = os dois métodos concordam. `exato` = recall 100% sem empate, mas sem confirmação por referência. `duplicado` = outro typecode casa melhor com esse mesmo tipo, logo o tipo real deste provavelmente não está no `fcs.def`.

| typecode | tipo | confiança | recall | por referência | registros | exemplo |
|---|---|---|---|---|---|---|
| 0 | `BUILDING` | CONFIRMADO | 70% | ref: BUILDING (1189) | 1148 | sign2- -clothes |
| 1 | `CHARACTER` | CONFIRMADO | 88% | ref: CHARACTER (1668) | 988 | Mercenary heavy |
| 2 | `WEAPON` | parcial | 93% | — | 68 | Katana |
| 3 | `ARMOUR` | CONFIRMADO | 92% | ref: ARMOUR (5100) | 257 | Mask 2 |
| 4 | `ITEM` | CONFIRMADO | 91% | ref: ITEM (2947) | 416 | Steel bars |
| 5 | `ANIMAL_ANIMATION` | CONFIRMADO | 100% | ref: ANIMAL_ANIMATION (254) | 68 | bull walk |
| 6 | `ATTACHMENT` | CONFIRMADO | 89% | ref: ATTACHMENT (372) | 103 | Haircut10-oldman |
| 7 | `RACE` | CONFIRMADO | 94% | ref: RACE (2493) | 99 | Garru |
| 10 | `FACTION` | CONFIRMADO | 95% | ref: FACTION (2202) | 161 | Medics Guild |
| 13 | `TOWN` | CONFIRMADO | 97% | ref: TOWN (472) | 436 | Bark |
| 16 | `LOCATIONAL_DAMAGE` | CONFIRMADO | 91% | ref: LOCATIONAL_DAMAGE (862) | 11 | Head |
| 17 | `COMBAT_TECHNIQUE` | parcial | 95% | — | 60 | Cut left static |
| 18 | `DIALOGUE` | CONFIRMADO | 90% | ref: DIALOGUE (3610) | nome: DIALOGUE | 2203 | Law enforcement defeats squad (arrest th |
| 19 | `DIALOGUE_LINE` | CONFIRMADO | 92% | ref: DIALOGUE_LINE (28701) | nome: DIALOGUE_LINE | 23889 | DIALOGUE_LINE6071 |
| 21 | `RESEARCH` | CONFIRMADO | 100% | ref: RESEARCH (257) | 275 | Heavy Building Foundations |
| 22 | `AI_TASK` | CONFIRMADO | 100% | ref: AI_TASK (1678) | 143 | get out of cage - escape |
| 24 | `ANIMATION` | CONFIRMADO | 100% | ref: ANIMATION (99) | 197 | idle_stand_relax |
| 25 | `STATS` | CONFIRMADO | 66% | ref: STATS (202) | 62 | hire medic |
| 26 | `PERSONALITY` | CONFIRMADO | 100% | ref: PERSONALITY (268) | 34 | bandit types |
| 27 | `CONSTANTS` | parcial | 97% | — | 3 | GLOBAL CONSTANTS |
| 28 | `BIOMES` | parcial | 96% | — | 137 | desert |
| 29 | `BUILDING_PART` | CONFIRMADO | 79% | ref: BUILDING_PART (1614) | nome: BARSIGN | 1464 | basic wall gate A |
| 31 | `DIALOG_ACTION` | POR NOME | 42% | nome: DIALOG_ACTION | 21225 | DIALOG_ACTION4205 |
| 43 | `REPEATABLE_BUILDING_PART_SLOT` | exato | 100% | — | 4 | hatches |
| 44 | `MATERIAL_SPEC` | exato | 100% | — | 259 | signs3_material |
| 45 | `MATERIAL_SPECS_COLLECTION` | exato | 100% | — | 11 | base buildings tiled |
| 46 | `CONTAINER` | CONFIRMADO | 100% | ref: CONTAINER (115) | 28 | Small Backpack |
| 47 | `MATERIAL_SPECS_CLOTHING` | exato | 100% | — | 170 | mask3 |
| 49 | `VENDOR_LIST` | CONFIRMADO | 100% | ref: VENDOR_LIST (720) | 187 | weapon vendor Outposts |
| 50 | `MATERIAL_SPECS_WEAPON` | exato | 100% | — | 49 | Edge Type 1 |
| 51 | `WEAPON_MANUFACTURER` | CONFIRMADO | 100% | ref: WEAPON_MANUFACTURER (656) | 18 | Truth Two |
| 52 | `SQUAD_TEMPLATE` | CONFIRMADO | 95% | ref: SQUAD_TEMPLATE (3313) | 1166 | Cannibal home guards |
| 53 | `GRASS` | duplicado | 25% | — | 3 | Northern desert |
| 55 | `COLOR_DATA` | CONFIRMADO | 100% | ref: COLOR_DATA (130) | 70 | super black |
| 56 | `GRASS` | duplicado | 60% | — | 1 | grass1 |
| 59 | `FOLIAGE_LAYER` | CONFIRMADO | 50% | ref: FOLIAGE_LAYER (1296) | 330 | Grass Spikey |
| 60 | `FOLIAGE_MESH` | CONFIRMADO | 98% | ref: FOLIAGE_MESH (843) | 945 | FOLIAGE_DUNE-Bouldersmall21 |
| 61 | `GRASS` | CONFIRMADO | 100% | ref: GRASS (36) | 42 | Basic Grass |
| 62 | `BUILDING_FUNCTIONALITY` | CONFIRMADO | 97% | ref: BUILDING_FUNCTIONALITY (279) | 136 | armour chain |
| 63 | `UNIQUE_SQUAD_TEMPLATE` | exato | 100% | — | 3 | bar |
| 64 | `NEW_GAME_STARTOFF` | exato | 100% | — | 23 | Rock Bottom |
| 68 | `WILDLIFE_BIRDS` | CONFIRMADO | 100% | ref: WILDLIFE_BIRDS (42) | 8 | BowlBirdsTEST |
| 69 | `MAP_FEATURES` | exato | 100% | — | 329 | UpthrustRocks01 |
| 70 | `DIPLOMATIC_ASSAULTS` | CONFIRMADO | 100% | ref: DIPLOMATIC_ASSAULTS (2) | 5 | Dust bandits |
| 71 | `SINGLE_DIPLOMATIC_ASSAULT` | CONFIRMADO | 100% | ref: SINGLE_DIPLOMATIC_ASSAULT (11) | 11 | raid filler |
| 72 | `AI_PACKAGE` | CONFIRMADO | 83% | ref: AI_PACKAGE (1511) | 275 | Diplomat Mission (running) |
| 73 | `DIALOGUE_PACKAGE` | CONFIRMADO | 100% | ref: DIALOGUE_PACKAGE (2585) | 385 | Npc Basic TOUGH |
| 74 | `GUN_DATA` | CONFIRMADO | 100% | ref: GUN_DATA (13) | 11 | Turret double |
| 76 | `ANIMAL_CHARACTER` | CONFIRMADO | 97% | ref: ANIMAL_CHARACTER (212) | 62 | Beak Thing |
| 77 | `UNIQUE_SQUAD_TEMPLATE` | CONFIRMADO | 96% | ref: UNIQUE_SQUAD_TEMPLATE (2) | 2 | UNIQUE bandit test |
| 78 | `FACTION_TEMPLATE` | exato | 100% | — | 4 | Ninja TEMPLATE |
| 80 | `WEATHER` | CONFIRMADO | 100% | ref: WEATHER (110) | 77 | WEATHER |
| 81 | `SEASON` | CONFIRMADO | 100% | ref: SEASON (79) | 59 | SEASON |
| 82 | `EFFECT` | CONFIRMADO | 91% | ref: EFFECT (377) | 126 | weather_volcano_smoke1 |
| 83 | `ITEM_PLACEMENT_GROUP` | exato | 100% | — | 30 | Food Ingridients |
| 84 | `WORD_SWAPS` | exato | 100% | — | 317 | DANG |
| 86 | `NEST_ITEM` | CONFIRMADO | 100% | ref: NEST_ITEM (117) | 20 | Beak Thing Egg |
| 87 | `CHARACTER_PHYSICS_ATTACHMENT` | CONFIRMADO | 100% | ref: CHARACTER_PHYSICS_ATTACHMENT (3) | 4 | Packbeast lantern |
| 88 | `LIGHT` | CONFIRMADO | 92% | ref: LIGHT (4) | 76 | white light |
| 89 | `HEAD` | CONFIRMADO | 100% | ref: HEAD (73) | 41 | HumanMale03 |
| 92 | `FOLIAGE_MESH` | duplicado | 94% | — | 2 | Iron Rock |
| 93 | `FACTION_CAMPAIGN` | CONFIRMADO | 97% | ref: FACTION_CAMPAIGN (408) | 295 | BASE- standard cannibal raid |
| 95 | `BIOME_GROUP` | CONFIRMADO | 100% | ref: BIOME_GROUP (265) | 92 | The Desert |
| 96 | `EFFECT_FOG_VOLUME` | CONFIRMADO | 100% | ref: EFFECT_FOG_VOLUME (8) | 10 | EFFECT_FOG_VOLUME |
| 97 | `FARM_DATA` | CONFIRMADO | 100% | ref: FARM_DATA (27) | 39 | Wheat Farm Type |
| 98 | `FARM_PART` | CONFIRMADO | 100% | ref: FARM_PART (76) | 18 | Crop_Base_part |
| 99 | `ENVIRONMENT_RESOURCES` | CONFIRMADO | 100% | ref: ENVIRONMENT_RESOURCES (70) | 26 | None |
| 100 | `RACE_GROUP` | exato | 100% | — | 11 | Fishman |
| 101 | `ARTIFACTS` | exato | 100% | — | 1 | ARTIFACTS |
| 102 | `MAP_ITEM` | CONFIRMADO | 100% | ref: MAP_ITEM (65) | 18 | Map of the Border Zone |
| 103 | `BUILDINGS_SWAP` | CONFIRMADO | 100% | ref: BUILDINGS_SWAP (93) | 40 | no carpets |
| 104 | `ITEMS_CULTURE` | CONFIRMADO | 100% | ref: ITEMS_CULTURE (60) | 12 | swamper |
| 105 | `ANIMATION_EVENT` | CONFIRMADO | 100% | ref: ANIMATION_EVENT (86) | 18 | Attack |
| 107 | `CROSSBOW` | CONFIRMADO | 94% | ref: CROSSBOW (116) | 11 | Ranger |
| 109 | `AMBIENT_SOUND` | CONFIRMADO | 100% | ref: AMBIENT_SOUND (55) | 27 | Auto Mine |
| 110 | `WORLD_EVENT_STATE` | CONFIRMADO | 100% | ref: WORLD_EVENT_STATE (1638) | 155 | Player is enemy of Shek Kingdom |
| 111 | `LIMB_REPLACEMENT` | CONFIRMADO | 92% | ref: LIMB_REPLACEMENT (163) | 48 | Human Left Arm Stump |
| 112 | `ANIMATION_FILE` | exato | 100% | — | 1 | base animations |
