"""Preparación acotada de atlas estacionales; no modifica las pinturas fuente."""
from PIL import Image, ImageChops, ImageFilter

VERSION = 'season-atlas-0.1.0'


def extend_rgb(image, tile_px, radius):
    """Propagar RGB a alfa cero por vecindad 8, sin cruzar límites de celda.

    Conserva todo RGB con alfa no nulo, incluida la franja antialias. La prioridad
    de vecinos es fija; cada paso lee exclusivamente el frente del paso anterior.
    No usa código de terceros aparte de las operaciones públicas de Pillow.
    """
    if (image.mode != 'RGBA' or min(image.size) < 1 or max(image.size) > 2048 or
            type(tile_px) is not int or tile_px < 1 or
            any(n % tile_px for n in image.size) or
            (image.width//tile_px)*(image.height//tile_px) > 64 or
            type(radius) is not int or not 0 <= radius <= 32):
        raise ValueError('Atlas/celda/radio incompatible o excesivo')
    result = image.copy()
    for top in range(0, image.height, tile_px):
        for left in range(0, image.width, tile_px):
            box = (left, top, left+tile_px, top+tile_px)
            tile = image.crop(box)
            rgb = tile.convert('RGB')
            known = tile.getchannel('A').point(lambda a: 255 if a else 0)
            for _ in range(radius):
                old_rgb, old_known = rgb.copy(), known.copy()
                for dx, dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
                    shifted = Image.new('L', tile.size)
                    shifted.paste(old_known, (dx, dy))
                    fresh = ImageChops.subtract(shifted, known)
                    color = Image.new('RGB', tile.size)
                    color.paste(old_rgb, (dx, dy))
                    rgb.paste(color, (0,0), fresh)
                    known = ImageChops.lighter(known, shifted)
            rgb.putalpha(tile.getchannel('A'))
            result.paste(rgb, box)
    return result


def compatible_pair(summer, autumn, tile_px=400, radius=16):
    if summer.size != autumn.size or summer.mode != 'RGBA' or autumn.mode != 'RGBA':
        raise ValueError('Pinturas con resolución o canales distintos')
    # Reparar exclusivamente RGB originalmente transparente que la máscara nueva
    # deja al descubierto. El RGB de pintura con alfa > 0 permanece exacto.
    filled = extend_rgb(autumn, tile_px, radius)
    missing = ImageChops.multiply(summer.getchannel('A').point(lambda x: 255 if x else 0),
                                 autumn.getchannel('A').point(lambda x: 0 if x else 255))
    coverage = Image.new('L', autumn.size)
    for y in range(0, autumn.height, tile_px):
        for x in range(0, autumn.width, tile_px):
            box = (x,y,x+tile_px,y+tile_px)
            known = autumn.getchannel('A').crop(box).point(lambda a:255 if a else 0)
            if radius:
                known = known.filter(ImageFilter.MaxFilter(2*radius+1))
            coverage.paste(known,box)
    if ImageChops.subtract(missing, coverage).getbbox():
        raise ValueError('RGB sin cobertura bajo la máscara común')
    compatible = autumn.copy()
    compatible.paste(filled, (0,0), missing)
    compatible.putalpha(summer.getchannel('A'))
    return summer.copy(), compatible
