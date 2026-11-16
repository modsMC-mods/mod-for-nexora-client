from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parent

COLORS = {
    11: {"base": (215, 165, 34), "dark": (139, 96, 13), "light": (255, 217, 95), "trim": (150, 90, 8)},
    12: {"base": (184, 196, 202), "dark": (101, 112, 118), "light": (228, 233, 239), "trim": (122, 134, 141)},
    13: {"base": (200, 186, 179), "dark": (118, 99, 98), "light": (240, 228, 220), "trim": (159, 145, 149)},
    14: {"base": (120, 70, 170), "dark": (64, 38, 94), "light": (177, 110, 220), "trim": (96, 56, 134)},
    15: {"base": (227, 200, 40), "dark": (140, 122, 6), "light": (246, 242, 110), "trim": (175, 150, 11)},
    16: {"base": (86, 206, 218), "dark": (23, 111, 128), "light": (163, 244, 252), "trim": (42, 158, 184)},
    17: {"base": (42, 157, 80), "dark": (19, 82, 39), "light": (116, 235, 150), "trim": (33, 122, 69)},
    18: {"base": (144, 114, 104), "dark": (65, 54, 53), "light": (203, 166, 156), "trim": (98, 84, 81)},
    19: {"base": (61, 101, 224), "dark": (17, 31, 130), "light": (147, 176, 255), "trim": (56, 74, 189)},
    20: {"base": (236, 235, 229), "dark": (128, 127, 128), "light": (255, 255, 255), "trim": (184, 187, 186)},
}

LEVELS = list(range(11, 21))


def solid(color, size=(16, 16)):
    img = Image.new("RGBA", size, color + (255,))
    return img


def draw_icon(slot_name: str, colors: dict, size=16):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    base = colors["base"]
    dark = colors["dark"]
    light = colors["light"]
    trim = colors["trim"]

    if slot_name == "helmet":
        draw.rectangle((3, 2, 12, 7), fill=base)
        draw.rectangle((4, 7, 11, 12), fill=light)
        draw.rectangle((5, 8, 10, 11), fill=dark)
        draw.rectangle((2, 3, 13, 4), fill=trim)
    elif slot_name == "chestplate":
        draw.rectangle((4, 2, 11, 13), fill=base)
        draw.rectangle((5, 3, 10, 7), fill=light)
        draw.rectangle((3, 6, 12, 9), fill=trim)
        draw.rectangle((5, 10, 10, 13), fill=dark)
    elif slot_name == "leggings":
        draw.rectangle((4, 2, 11, 12), fill=base)
        draw.rectangle((5, 3, 10, 8), fill=light)
        draw.rectangle((5, 9, 10, 12), fill=dark)
        draw.line((6, 13, 9, 13), fill=trim, width=2)
    elif slot_name == "boots":
        draw.rectangle((4, 6, 11, 13), fill=base)
        draw.rectangle((5, 5, 10, 6), fill=light)
        draw.rectangle((4, 12, 11, 15), fill=dark)
        draw.rectangle((6, 8, 9, 9), fill=trim)

    draw.rectangle((0, 0, size - 1, size - 1), outline=(20, 20, 20, 180), width=1)
    return img


def draw_armor_layer(slot_name: str, colors: dict, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    base = colors["base"]
    dark = colors["dark"]
    light = colors["light"]
    trim = colors["trim"]

    if slot_name == "helmet":
        draw.rounded_rectangle((14, 2, 50, 22), radius=5, fill=base)
        draw.rounded_rectangle((18, 18, 46, 42), radius=5, fill=light)
        draw.rectangle((22, 22, 42, 34), fill=dark)
        draw.rectangle((18, 42, 46, 48), fill=dark)
        draw.rectangle((8, 10, 14, 24), fill=trim)
        draw.rectangle((50, 10, 56, 24), fill=trim)
    elif slot_name == "chestplate":
        draw.rounded_rectangle((16, 12, 48, 54), radius=6, fill=base)
        draw.rounded_rectangle((20, 18, 44, 28), radius=4, fill=light)
        draw.rounded_rectangle((18, 32, 46, 46), radius=4, fill=dark)
        draw.rectangle((14, 14, 18, 52), fill=trim)
        draw.rectangle((46, 14, 50, 52), fill=trim)
        draw.rectangle((26, 48, 38, 54), fill=trim)
    elif slot_name == "leggings":
        draw.rounded_rectangle((18, 12, 46, 54), radius=6, fill=base)
        draw.rectangle((22, 18, 42, 28), fill=light)
        draw.rectangle((22, 32, 42, 42), fill=dark)
        draw.rectangle((18, 12, 24, 54), fill=trim)
        draw.rectangle((40, 12, 46, 54), fill=trim)
        draw.rectangle((24, 52, 40, 54), fill=trim)
    elif slot_name == "boots":
        draw.rounded_rectangle((18, 24, 46, 56), radius=6, fill=base)
        draw.rounded_rectangle((22, 14, 42, 24), radius=4, fill=light)
        draw.rectangle((18, 54, 46, 58), fill=dark)
        draw.rectangle((20, 24, 24, 56), fill=trim)
        draw.rectangle((40, 24, 44, 56), fill=trim)

    # kontur i glowne detale
    draw.rectangle((0, 0, size - 1, size - 1), outline=(40, 40, 40, 180), width=2)
    return img


def create_pack_png():
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((12, 12, 116, 116), radius=16, fill=(26, 26, 35, 255))
    draw.rounded_rectangle((20, 20, 108, 108), radius=12, fill=(52, 52, 60, 255))
    draw.regular_polygon((64, 64, 30), 6, rotation=30, fill=(210, 175, 80, 255))
    draw.regular_polygon((64, 64, 18), 4, rotation=45, fill=(255, 220, 120, 255))
    img.save(ROOT / "pack.png")


def generate_textures():
    create_pack_png()

    item_root = ROOT / "textures" / "item"
    item_root.mkdir(parents=True, exist_ok=True)
    humanoid_root = ROOT / "textures" / "entity" / "equipment" / "humanoid"
    humanoid_root.mkdir(parents=True, exist_ok=True)
    leggings_root = ROOT / "textures" / "entity" / "equipment" / "humanoid_leggings"
    leggings_root.mkdir(parents=True, exist_ok=True)

    for level in LEVELS:
        colors = COLORS[level]
        for slot in ["helmet", "chestplate", "leggings", "boots"]:
            icon = draw_icon(slot, colors, size=16)
            icon.save(item_root / f"{slot}_lvl_{level}.png")

            layer = draw_armor_layer(slot, colors, size=64)
            if slot in {"helmet", "chestplate"}:
                layer.save(humanoid_root / f"lvl_{level}.png")
            else:
                layer.save(leggings_root / f"lvl_{level}.png")

    # dodatkowy asset dla armor setu w stylu vanilla, z prostym warstwowym layout
    for level in LEVELS:
        colors = COLORS[level]
        for slot in ["helmet", "chestplate", "leggings", "boots"]:
            icon = draw_icon(slot, colors, size=16)
            icon.save(item_root / f"{slot}_lvl_{level}.png")

        # w zaleznosci od slotu tworzony jest tylko jeden obraz warstwy dla kazdego seta
        # humanoid i humanoid_leggings moga byc uzyte w zbroji z linii prostego itemu
        body_layer = draw_armor_layer("chestplate", colors, size=64)
        body_layer.save(humanoid_root / f"lvl_{level}.png")
        legs_layer = draw_armor_layer("leggings", colors, size=64)
        legs_layer.save(leggings_root / f"lvl_{level}.png")

    print("Generated LevelGear textures in:", ROOT)


if __name__ == "__main__":
    generate_textures()
