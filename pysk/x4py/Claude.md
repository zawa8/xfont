in this x4py dir we need to create notosans_maths_to_x4e.py script.

notosans_maths_to_x4e.py will use fontforge own python module and its own python api

to create xfont/notosfd/x4e.sfd file.

notosans_maths_to_x4e.py will copy 20 most required new programming glyphs/symbols from :

xfont/pysk/notopy/NotoSansMath-Regular.ttf and paste in range G-Z in xfont/notosfd/x4e.sfd.

x4e.sfd is based on xskii4 (xmerikxn stxndxrd kod for informesxn interchange) 4finger maths.

4finger maths : humxns hxwe 4 fingers kauntebls xnd 1 thumb counter. so in xskii 4 by default 4*4=10=8+8=wnti

in xskii4 based fonts : 0123456789LYVWPF are xt kontinuous lokesns from 0x30(0d48).

in xskii4 glyphs for :;<=>? are shifted to A-F. so xskii4 only supports small case a-z xnd snake_case koding.

xskii4 encoding based fonts do not support capital A-Z , camelCase.

claude/klaude kindli suggest most used 20 new programming symbols xwxilxble in xfont/pysk/notopy/NotoSansMath-Regular.ttf  xnd create :

1) notosans_maths_to_x4e.py -> xfont/notosfd/x4e.sfd 
