python3 .\tools\scripts\font.py create --ttf-path "fonts\VD-giga JR Std B_0.ttf" --charset-path ".\temp\us_english.txt" --gtbl-path ".\temp\occ_glyphtable.buct" --bfnt-path-fmt ".\temp\occ_{}.bfont" --mtxt-path ".\temp\occ_atlas.bctex" --mtxt-width 4096 --mtxt-height 2048 --gtbl-path-ingame "system/fonts/symbols/occ_glyphtable.buct" --mtxt-path-ingame "system/fonts/textures/occ_atlas.bctex" --20 .\temp\us_english.txt --20-useicon --32 .\temp\us_english.txt --32-useicon --42 .\temp\us_english.txt --42-useicon --52 .\temp\us_english.txt 
.\tools\bin\mtxttool.exe -ig .\temp\occ_atlas.png -t .\temp\occ_atlas.bctex .\temp\origin\Romfs\textures\system\fonts\textures\chc_atlas.bctex

set FONTDIR=temp\010093801237C000\romfs\system\fonts
set SYMDIR=%FONTDIR%\symbols
set TEXDIR=temp\010093801237C000\romfs\textures\system\fonts\textures
md %SYMDIR%
md %TEXDIR%

move ".\temp\occ_glyphtable.buct" %SYMDIR%
move ".\temp\occ_*.bfont" %FONTDIR%
move ".\temp\occ_atlas.bctex" %TEXDIR%