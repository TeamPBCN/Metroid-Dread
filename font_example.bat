python3 .\tools\scripts\font.py create --ttf-path ".\temp\fzmh.ttf" --charset-path ".\temp\simplified_chinese.txt" --gtbl-path ".\temp\chc_glyphtable.buct" --bfnt-path-fmt ".\temp\chc_{}.bfont" --mtxt-path ".\temp\chc_atlas.bctex" --mtxt-width 4096 --mtxt-height 2048 --gtbl-path-ingame "system/fonts/symbols/chc_glyphtable.buct" --mtxt-path-ingame "system/fonts/textures/chc_atlas.bctex" --32 .\temp\simplified_chinese.txt --52 .\temp\simplified_chinese.txt --32-useicon
.\tools\bin\mtxttool.exe -ig .\temp\chc_atlas.png -t .\temp\chc_atlas.bctex .\temp\orign\Romfs\textures\system\fonts\textures\chc_atlas.bctex

set FONTDIR=temp\010093801237C000\romfs\system\fonts
set SYMDIR=%FONTDIR%\symbols
set TEXDIR=temp\010093801237C000\romfs\textures\system\fonts\textures
md %SYMDIR%
md %TEXDIR%

move ".\temp\chc_glyphtable.buct" %SYMDIR%
move ".\temp\chc_*.bfont" %FONTDIR%
move ".\temp\chc_atlas.bctex" %TEXDIR%