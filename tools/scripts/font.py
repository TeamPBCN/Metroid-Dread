import struct
import sys
import os
from os import SEEK_SET
from io import BytesIO

import freetype
import greedypacker
from freetype import FT_LOAD_FLAGS, Face
from PIL import Image


ICONS = {
    0x1800: (-1, 30, 34),
    0x1801: (-1, 30, 34),
    0x1802: (-1, 30, 34),
    0x1803: (-1, 30, 34),
    0x1804: (-1, 30, 34),
    0x1805: (-1, 30, 34),
    0x1806: (-1, 30, 34),
    0x1807: (-1, 30, 34),
    0x1808: (-1, 30, 34),
    0x1809: (-1, 30, 34),
    0x180a: (-1, 30, 34),
    0x180b: (-1, 30, 34),
    0x180c: (-1, 30, 34),
    0x180d: (-1, 30, 34),
    0x180e: (-1, 30, 34),
    0x180f: (-1, 30, 34),
    0x1810: (-1, 30, 34),
    0x1811: (-1, 39, 52),
    0x1812: (-1, 30, 34),
    0x1813: (-1, 30, 34),
    0x1815: (-1, 30, 34),
    0x1816: (-1, 39, 52),
    0x1817: (-1, 39, 52),
    0x1818: (-1, 39, 52),
    0x1819: (-1, 39, 52),
    0x181a: (-1, 39, 52),
    0x181b: (-1, 39, 52),
    0x181c: (-1, 39, 52),
    0x181d: (-1, 36, 47),
    0x181e: (-1, 59, 92),
    0x181f: (-1, 59, 92),
    0x1820: (-1, 59, 92),
    0x1821: (-1, 36, 47),
    0x1822: (-1, 59, 92),
    0x1823: (-1, 59, 92),
    0x1824: (-1, 59, 92),
    0x1825: (-1, 39, 52),
    0x1826: (-1, 59, 92),
    0x1827: (-1, 59, 92),
    0x1828: (-1, 59, 92),
    0x1829: (-1, 30, 34),
    0x182a: (-1, 39, 52),
    0x182e: (-1, 30, 34),
    0x182f: (-14, 41, 32),
    0x1830: (-14, 41, 32),
    0x1832: (-1, 30, 34),
    0x1834: (-14, 41, 32),
    0x1837: (-1, 30, 34),
    0x1838: (-1, 30, 34),
    0x1839: (-1, 30, 34),
    0x1840: (-1, 30, 34),
    0x1841: (-1, 30, 34),
}


def f26d6_to_int(val):
    ret = (abs(val) & 0x7FFFFFC0) >> 6
    if val < 0:
        return -ret
    else:
        return ret


class MetroidFontGlyph(object):
    def __init__(self) -> None:
        super().__init__()
        self.image = Image.new(mode='RGBA', size=(4, 4))
        self.packer_item = greedypacker.Item(4, 4)
        self.xoffset = 0
        self.yoffset = 0
        self.xadv = 0

    @property
    def packed_left(self):
        return self.packer_item.x

    @property
    def packed_top(self):
        return self.packer_item.y

    @property
    def packed_right(self):
        return self.packed_left+self.packer_item.width

    @property
    def packed_bottom(self):
        return self.packed_top+self.packer_item.height

    @staticmethod
    def empty():
        return MetroidFontGlyph()

    @staticmethod
    def new(c, font: Face):
        mfg = MetroidFontGlyph()

        flags = FT_LOAD_FLAGS['FT_LOAD_RENDER'] | FT_LOAD_FLAGS['FT_LOAD_NO_HINTING'] | FT_LOAD_FLAGS['FT_LOAD_NO_HINTING']
        font.load_char(c, flags)

        glyphslot = font.glyph
        bitmap = glyphslot.bitmap
        adv = f26d6_to_int(glyphslot.metrics.horiAdvance)
        horiBearingX = f26d6_to_int(glyphslot.metrics.horiBearingX)
        horiBearingY = f26d6_to_int(glyphslot.metrics.horiBearingY)
        gheight = f26d6_to_int(glyphslot.metrics.height)

        if bitmap.width == 0 or bitmap.rows == 0:
            mfg.image = Image.new(mode='LA', size=(4, 4))
        else:
            pixel_data = struct.pack(
                'B'*len(bitmap.buffer)*2, *(x for pix in ((a, a) for a in bitmap.buffer) for x in pix))
            mfg.image = Image.frombuffer(mode='LA', size=(
                bitmap.width, bitmap.rows), data=pixel_data)

        mfg.packer_item = greedypacker.Item(
            mfg.image.width, mfg.image.height, rotation=False)

        mfg.xoffset = horiBearingX
        mfg.yoffset = horiBearingY
        mfg.xadv = adv

        return mfg

    @staticmethod
    def new_icon(icon_id):
        mfg = MetroidFontGlyph()
        icon_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'icons', '%04x.png' % ord(icon_id))
        if os.path.isfile(icon_path):
            mfg.image = Image.open(icon_path)
            mfg.packer_item = greedypacker.Item(
                mfg.image.width, mfg.image.height, rotation=False)
            mfg.xoffset = -1
            mfg.yoffset = 30
            mfg.xadv = 34
            return mfg
        else:
            raise FileNotFoundError(icon_path)


class MetroidFont(object):
    HEADER_STRUCTURE = '4sBBBBqiihhiiiqq'

    def __init__(self) -> None:
        super().__init__()
        self.magic = b'MFNT'
        self.version = (1, 0, 10, 0)
        self.texture_path_offset = 0x38
        self.texture_size = (0, 0)
        self.unk1, self.unk2 = (2, -1)
        self.font_size = 0
        self.glyph_count = 0
        self.unk3 = -1
        self.glyph_data_offset = 0
        self.glyph_table_path = 0
        self.glyphs = {}

        self.font_face = None
        self.__filter__ = ''

    def init_fontface(self, path):
        self.font_face = Face(path)
        self.font_face.set_pixel_sizes(self.font_size, self.font_size)

    def add_char(self, c):
        if (not self.__filter__ or c in self.__filter__):
            glyph = MetroidFontGlyph.new(c, self.font_face)
        else:
            glyph = MetroidFontGlyph.empty()
        self.glyphs[c] = glyph
        self.glyph_count = len(self.glyphs)
        return glyph

    @property
    def filter(self):
        return self.__filter__

    @filter.setter
    def filter(self, value: str):
        self.__filter__ = sorted(value)

    @property
    def texture_width(self):
        return self.texture_size[0]

    @texture_width.setter
    def texture_width(self, value: int):
        self.texture_size[0] = value

    @property
    def texture_height(self):
        return self.texture_size[1]

    @texture_height.setter
    def texture_height(self, value: int):
        self.texture_size[1] = value

    @staticmethod
    def new(font_size, font_path, texture_size, chars_filter):
        mfnt = MetroidFont()

        mfnt.font_size = font_size+4
        mfnt.texture_size = texture_size
        mfnt.filter = chars_filter
        mfnt.init_fontface(font_path)

        return mfnt


class MetroidFontCollection(object):
    def __init__(self) -> None:
        super().__init__()

        self.fonts = {}
        self.chars = []
        self.icons = {}

        self.texture_size = (0, 0)
        self.font_path = ''

    def add_char(self, c):
        if c in self.chars:
            return

        self.chars.append(c)
        for k in self.fonts.keys():
            font = self.fonts[k]
            font.add_char(c)

    def add_font(self, size, filter, font_path=None, use_icon=False):
        if not font_path:
            font_path = self.font_path
        mfnt = MetroidFont.new(
            size, font_path, self.texture_size, filter)
        self.fonts[size] = mfnt
        if use_icon:
            print('Use icon')
            for k in self.icons:
                mfnt.glyphs[k] = self.icons[k]

    def remap(self):
        print('Remapping...')
        glyphs = (glyph for glyphs in (font.glyphs.values()
                  for font in self.fonts.values()) for glyph in glyphs)
        bin_man = greedypacker.BinManager(
            self.texture_size[0], self.texture_size[1], pack_algo='skyline', heuristic='bottom_left', rotation=False)
        bin_man.add_items(*(glyph.packer_item for glyph in glyphs))
        bin_man.execute()

        if len(bin_man.bins) > 1:
            raise ValueError(
                "Too many chars, try to trim the font size using filters")

    def save(self, glyph_table_path: str, bfont_path_format: str, texture_path: str,
             glyph_table_path_in_game: str = None, texture_path_in_game: str = None):
        chars = sorted(self.chars)
        chars.extend(sorted(self.icons.keys()))
        self.remap()

        # Save glyph table
        with open(glyph_table_path, 'wb') as buct:
            # Write header
            buct.write(struct.pack('<4sbbbbiiq', b'MUCT', *(1, 0, 4, 0),
                       len(chars), -1, 0x18))
            for i in range(len(chars)):
                buct.write(struct.pack('<Hhi', ord(chars[i]), -1, i))

        # Save bfonts
        for k in self.fonts.keys():
            path = bfont_path_format.format(k)
            font: MetroidFont = self.fonts[k]
            with open(path, 'wb') as bfont:
                # Write header
                bfont.write(struct.pack(
                    '<'+MetroidFont.HEADER_STRUCTURE, font.magic, *font.version,
                    font.texture_path_offset, *font.texture_size,
                    font.unk1, font.unk2, font.font_size, font.glyph_count, font.unk3,
                    font.glyph_data_offset, font.glyph_table_path))

                font.texture_path_offset = bfont.tell()
                if texture_path_in_game:
                    bfont.write(texture_path_in_game.encode('utf-8'))
                else:
                    bfont.write(texture_path.encode('utf-8'))
                bfont.write(b'\x00')
                # align?
                while bfont.tell() % 0x10 != 0:
                    bfont.write(b'\xFF')
                font.glyph_data_offset = bfont.tell()

                for c in chars:
                    if c not in font.glyphs:
                        break  # Should break
                    glyph: MetroidFontGlyph = font.glyphs[c]
                    bfont.write(struct.pack('<hhhhhhh', glyph.packer_item.x, glyph.packer_item.y,
                                glyph.packer_item.width, glyph.packer_item.height, glyph.xoffset, glyph.yoffset, glyph.xadv))
                font.glyph_table_path = bfont.tell()
                if glyph_table_path_in_game:
                    bfont.write(glyph_table_path_in_game.encode('utf-8'))
                else:
                    bfont.write(glyph_table_path.encode('utf-8'))
                bfont.write(b'\x00')

                bfont.seek(0, SEEK_SET)
                # Write updated header
                bfont.write(struct.pack(
                    '<'+MetroidFont.HEADER_STRUCTURE, font.magic, *font.version,
                    font.texture_path_offset, *font.texture_size,
                    font.unk1, font.unk2, font.font_size, font.glyph_count, font.unk3,
                    font.glyph_data_offset, font.glyph_table_path))

        # Save texture
        glyphs = (glyph for glyphs in (font.glyphs.values()
                  for font in self.fonts.values()) for glyph in glyphs)
        tex = Image.new(mode='RGBA', size=self.texture_size)
        for glyph in glyphs:
            tex.paste(glyph.image, (glyph.packed_left, glyph.packed_top,
                      glyph.packed_right, glyph.packed_bottom))
        # Save as png first
        tex.save(texture_path.replace('.bctex', '.png'))

    @staticmethod
    def new(font_path, texture_size):
        mfc = MetroidFontCollection()
        mfc.font_path = font_path
        mfc.texture_size = texture_size

        # Load icons
        for i in ICONS.keys():
            c = chr(i)
            icon = MetroidFontGlyph.new_icon(c)
            icon.xoffset = ICONS[i][0]
            icon.yoffset = ICONS[i][1]
            icon.xadv = ICONS[i][2]

            mfc.icons[c] = icon

        return mfc


class Actions(object):
    @staticmethod
    def create(ttf_path, charset_path, gtbl_path, bfnt_path_fmt, mtxt_path, mtxt_width, mtxt_height,
               gtbl_path_ingame=None, mtxt_path_ingame=None, **kwargs):
        mfnc = MetroidFontCollection.new(ttf_path, (mtxt_width, mtxt_height))
        for kw in kwargs:
            if '_ttf' in kw or '_useicon' in kw:
                continue

            size = int(kw)
            filter = open(kwargs[kw], 'r', encoding='utf-16').read()
            font_path = None
            if kw+'_ttf' in kwargs:
                font_path = kwargs[kw+'_ttf']
            print('Add font size: %d, filter: %s' % (size, kwargs[kw]))
            mfnc.add_font(size, filter, font_path, kw+'_useicon' in kwargs)

        i = 1
        charset = set((c for c in open(charset_path, 'r',
                      encoding='utf-16').read() if ord(c) not in ICONS))
        for c in charset:
            sys.stdout.write("Adding chars...(%d/%d)\r" % (i, len(charset)))
            mfnc.add_char(c)
            i += 1
        print('')

        mfnc.save(gtbl_path, bfnt_path_fmt, mtxt_path,
                  gtbl_path_ingame, mtxt_path_ingame)


if __name__ == '__main__':
    import fire
    fire.Fire(Actions)
