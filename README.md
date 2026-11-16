# LevelGear

Resource pack dla Minecraft Java 1.21.11.

Wersja formatu: `min_format` = `88`, `max_format` = `88`.

## Struktura

- `pack.mcmeta`
- `generate_textures.py` – skrypt Pillow generujacy tekstury, `pack.png`, ikony itemow oraz warstwy zbroi.
- `assets/minecraft/items/netherite_sword.json` – custom model data dla mieczy poziomow 11-20.
- `assets/minecraft/equipment/set_lvl_11.json` ... `set_lvl_20.json` – asset ID zbroi.
- `textures/item/` – ikony setow zbroi generowane automatycznie.
- `textures/entity/equipment/humanoid/` i `textures/entity/equipment/humanoid_leggings/` – warstwy zbroi do renderowania.

## Poziomy i modele miecza

| Poziom | CustomModelData | Model | Asset ID zbroi |
| --- | ---: | --- | --- |
| 11 | 11 | `minecraft:item/gold_ingot` | `minecraft:set_lvl_11` |
| 12 | 12 | `minecraft:item/iron_ingot` | `minecraft:set_lvl_12` |
| 13 | 13 | `minecraft:item/quartz` | `minecraft:set_lvl_13` |
| 14 | 14 | `minecraft:item/purple_dye` | `minecraft:set_lvl_14` |
| 15 | 15 | `minecraft:item/yellow_dye` | `minecraft:set_lvl_15` |
| 16 | 16 | `minecraft:item/diamond` | `minecraft:set_lvl_16` |
| 17 | 17 | `minecraft:item/green_dye` | `minecraft:set_lvl_17` |
| 18 | 18 | `minecraft:item/netherite_ingot` | `minecraft:set_lvl_18` |
| 19 | 19 | `minecraft:item/lapis_lazuli` | `minecraft:set_lvl_19` |
| 20 | 20 | `minecraft:item/white_dye` | `minecraft:set_lvl_20` |

## Test commands

```text
/give @p minecraft:netherite_sword[custom_model_data=11] 1
/give @p minecraft:netherite_sword[custom_model_data=12] 1
/give @p minecraft:netherite_sword[custom_model_data=13] 1
/give @p minecraft:netherite_sword[custom_model_data=14] 1
/give @p minecraft:netherite_sword[custom_model_data=15] 1
/give @p minecraft:netherite_sword[custom_model_data=16] 1
/give @p minecraft:netherite_sword[custom_model_data=17] 1
/give @p minecraft:netherite_sword[custom_model_data=18] 1
/give @p minecraft:netherite_sword[custom_model_data=19] 1
/give @p minecraft:netherite_sword[custom_model_data=20] 1
```

```text
/give @p minecraft:diamond_helmet[custom_model_data=11,equippable={slot:"head",asset_id:"minecraft:set_lvl_11"}] 1
/give @p minecraft:diamond_chestplate[custom_model_data=11,equippable={slot:"chest",asset_id:"minecraft:set_lvl_11"}] 1
/give @p minecraft:diamond_leggings[custom_model_data=11,equippable={slot:"legs",asset_id:"minecraft:set_lvl_11"}] 1
/give @p minecraft:diamond_boots[custom_model_data=11,equippable={slot:"feet",asset_id:"minecraft:set_lvl_11"}] 1
```

Powtorz dla poziomow 12-20, zmieniajac `custom_model_data` i `asset_id`.

## Uruchomienie skryptu

```bash
python3 generate_textures.py
```

Skrypt wygeneruje:
- `pack.png`
- `textures/item/helmet_lvl_11.png`, `helmet_lvl_12.png`, ...
- `textures/item/chestplate_lvl_11.png`, ...
- `textures/item/leggings_lvl_11.png`, ...
- `textures/item/boots_lvl_11.png`, ...
- `textures/entity/equipment/humanoid/lvl_11.png`, ...
- `textures/entity/equipment/humanoid_leggings/lvl_11.png`, ...

Uwaga: w Minecraft Java 1.21.11 format packu korzysta z `min_format` / `max_format`, i dla tej wersji przyjmuje sie `88`.
