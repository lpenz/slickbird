'''Stream a collection to a fd in json format'''
import json


def collectionjson(cdb, ofd):
    def o(d):
        ofd.write(str(d).encode('utf-8'))

    o('[\n')
    gfirst = True
    for gdb in cdb.games:
        if not gfirst:
            o(',\n')
        gfirst = False
        o('{ "game": ')
        o(json.dumps(gdb.as_dict(), sort_keys=True))
        o(',\n  "variants": [\n')
        vfirst = True
        for vdb in gdb.variants:
            if not vfirst:
                o(',\n')
            vfirst = False
            vfirst = False
            o('      { "variant": ')
            o(json.dumps(vdb.as_dict(), sort_keys=True))
            o(',\n        "roms":  [ ')
            rfirst = True
            for rdb in vdb.roms:
                if not rfirst:
                    o(',\n                   ')
                rfirst = False
                o(json.dumps(rdb.as_dict(), sort_keys=True))
            o(']}')
        o(']}')
    o('\n]\n')
