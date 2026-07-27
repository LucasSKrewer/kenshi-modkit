# Mapa de typecodes

Gerado por `python typecodes.py`, correlacionando os campos dos registros de `data/` com as seções do `fcs.def` do jogo.

`recall` = fração dos campos vistos que o tipo do fcs.def explica. `exato` = recall 100% e sem empate.

| typecode | tipo | confiança | recall | registros | exemplo |
|---|---|---|---|---|---|
| 0 | `BUILDING` | parcial | 70% | 1148 | sign2- -clothes |
| 1 | `CHARACTER` | parcial | 88% | 988 | Mercenary heavy |
| 2 | `WEAPON` | parcial | 93% | 68 | Katana |
| 3 | `ARMOUR` | parcial | 92% | 257 | Mask 2 |
| 4 | `ITEM` | parcial | 91% | 416 | Steel bars |
| 5 | `ANIMAL_ANIMATION` | exato | 100% | 68 | bull walk |
| 6 | `ATTACHMENT` | parcial | 89% | 103 | Haircut10-oldman |
| 7 | `RACE` | parcial | 94% | 99 | Garru |
| 10 | `FACTION` | parcial | 95% | 161 | Medics Guild |
| 13 | `TOWN` | parcial | 97% | 436 | Bark |
| 16 | `LOCATIONAL_DAMAGE` | parcial | 91% | 11 | Head |
| 17 | `COMBAT_TECHNIQUE` | parcial | 95% | 60 | Cut left static |
| 18 | `DIALOGUE` | parcial | 90% | 2203 | Law enforcement defeats squad (arrest th |
| 19 | `DIALOGUE_LINE` | parcial | 92% | 23889 | DIALOGUE_LINE6071 |
| 21 | `RESEARCH` | exato | 100% | 275 | Heavy Building Foundations |
| 22 | `AI_TASK` | exato | 100% | 143 | get out of cage - escape |
| 24 | `ANIMATION` | exato | 100% | 197 | idle_stand_relax |
| 25 | `STATS` | parcial | 66% | 62 | hire medic |
| 26 | `PERSONALITY` | exato | 100% | 34 | bandit types |
| 27 | `CONSTANTS` | parcial | 97% | 3 | GLOBAL CONSTANTS |
| 28 | `BIOMES` | parcial | 96% | 137 | desert |
| 29 | `BUILDING_PART` | parcial | 79% | 1464 | basic wall gate A |
| 31 | `AI_PACKAGE` | duplicado | 42% | 21225 | DIALOG_ACTION4205 |
| 43 | `REPEATABLE_BUILDING_PART_SLOT` | exato | 100% | 4 | hatches |
| 44 | `MATERIAL_SPEC` | exato | 100% | 259 | signs3_material |
| 45 | `MATERIAL_SPECS_COLLECTION` | exato | 100% | 11 | base buildings tiled |
| 46 | `CONTAINER` | exato | 100% | 28 | Small Backpack |
| 47 | `MATERIAL_SPECS_CLOTHING` | exato | 100% | 170 | mask3 |
| 49 | `VENDOR_LIST` | exato | 100% | 187 | weapon vendor Outposts |
| 50 | `MATERIAL_SPECS_WEAPON` | exato | 100% | 49 | Edge Type 1 |
| 51 | `WEAPON_MANUFACTURER` | exato | 100% | 18 | Truth Two |
| 52 | `SQUAD_TEMPLATE` | parcial | 95% | 1166 | Cannibal home guards |
| 53 | `GRASS` | duplicado | 25% | 3 | Northern desert |
| 55 | `COLOR_DATA` | exato | 100% | 70 | super black |
| 56 | `GRASS` | duplicado | 60% | 1 | grass1 |
| 59 | `FOLIAGE_LAYER` | parcial | 50% | 330 | Grass Spikey |
| 60 | `FOLIAGE_MESH` | parcial | 98% | 945 | FOLIAGE_DUNE-Bouldersmall21 |
| 61 | `GRASS` | exato | 100% | 42 | Basic Grass |
| 62 | `BUILDING_FUNCTIONALITY` | parcial | 97% | 136 | armour chain |
| 63 | `UNIQUE_SQUAD_TEMPLATE` | exato | 100% | 3 | bar |
| 64 | `NEW_GAME_STARTOFF` | exato | 100% | 23 | Rock Bottom |
| 68 | `WILDLIFE_BIRDS` | exato | 100% | 8 | BowlBirdsTEST |
| 69 | `MAP_FEATURES` | exato | 100% | 329 | UpthrustRocks01 |
| 70 | `DIPLOMATIC_ASSAULTS` | exato | 100% | 5 | Dust bandits |
| 71 | `SINGLE_DIPLOMATIC_ASSAULT` | exato | 100% | 11 | raid filler |
| 72 | `AI_PACKAGE` | parcial | 83% | 275 | Diplomat Mission (running) |
| 73 | `DIALOGUE_PACKAGE` | exato | 100% | 385 | Npc Basic TOUGH |
| 74 | `GUN_DATA` | exato | 100% | 11 | Turret double |
| 76 | `ANIMAL_CHARACTER` | parcial | 97% | 62 | Beak Thing |
| 77 | `UNIQUE_SQUAD_TEMPLATE` | duplicado | 96% | 2 | UNIQUE bandit test |
| 78 | `FACTION_TEMPLATE` | exato | 100% | 4 | Ninja TEMPLATE |
| 80 | `WEATHER` | exato | 100% | 77 | WEATHER |
| 81 | `SEASON` | exato | 100% | 59 | SEASON |
| 82 | `EFFECT` | parcial | 91% | 126 | weather_volcano_smoke1 |
| 83 | `ITEM_PLACEMENT_GROUP` | exato | 100% | 30 | Food Ingridients |
| 84 | `WORD_SWAPS` | exato | 100% | 317 | DANG |
| 86 | `NEST_ITEM` | exato | 100% | 20 | Beak Thing Egg |
| 87 | `CHARACTER_PHYSICS_ATTACHMENT` | exato | 100% | 4 | Packbeast lantern |
| 88 | `LIGHT` | parcial | 92% | 76 | white light |
| 89 | `HEAD` | exato | 100% | 41 | HumanMale03 |
| 92 | `FOLIAGE_MESH` | duplicado | 94% | 2 | Iron Rock |
| 93 | `FACTION_CAMPAIGN` | parcial | 97% | 295 | BASE- standard cannibal raid |
| 95 | `BIOME_GROUP` | exato | 100% | 92 | The Desert |
| 96 | `EFFECT_FOG_VOLUME` | exato | 100% | 10 | EFFECT_FOG_VOLUME |
| 97 | `FARM_DATA` | exato | 100% | 39 | Wheat Farm Type |
| 98 | `FARM_PART` | exato | 100% | 18 | Crop_Base_part |
| 99 | `ENVIRONMENT_RESOURCES` | exato | 100% | 26 | None |
| 100 | `RACE_GROUP` | exato | 100% | 11 | Fishman |
| 101 | `ARTIFACTS` | exato | 100% | 1 | ARTIFACTS |
| 102 | `MAP_ITEM` | exato | 100% | 18 | Map of the Border Zone |
| 103 | `BUILDINGS_SWAP` | exato | 100% | 40 | no carpets |
| 104 | `ITEMS_CULTURE` | exato | 100% | 12 | swamper |
| 105 | `ANIMATION_EVENT` | exato | 100% | 18 | Attack |
| 107 | `CROSSBOW` | parcial | 94% | 11 | Ranger |
| 109 | `AMBIENT_SOUND` | exato | 100% | 27 | Auto Mine |
| 110 | `WORLD_EVENT_STATE` | exato | 100% | 155 | Player is enemy of Shek Kingdom |
| 111 | `LIMB_REPLACEMENT` | parcial | 92% | 48 | Human Left Arm Stump |
| 112 | `ANIMATION_FILE` | exato | 100% | 1 | base animations |
