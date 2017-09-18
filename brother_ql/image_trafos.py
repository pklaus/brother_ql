from PIL import Image
import colorsys

def HLSColor(img):
    """ https://stackoverflow.com/a/22237709/183995 """
    if isinstance(img,Image.Image):
        img = img.convert('RGB')
        r,g,b = img.split()
        Hdat = []
        Ldat = []
        Sdat = []
        for rd,gn,bl in zip(r.getdata(),g.getdata(),b.getdata()) :
            h,l,s = colorsys.rgb_to_hls(rd/255.,gn/255.,bl/255.)
            Hdat.append(int(h*255.))
            Ldat.append(int(l*255.))
            Sdat.append(int(s*255.))
        r.putdata(Hdat)
        g.putdata(Ldat)
        b.putdata(Sdat)
        return Image.merge('RGB',(r,g,b))
    else:
        return None

def filtered_hls(im, filter_h, filter_l, filter_s, default_col=(255,255,255)):
    hls_im = HLSColor(im)

    H, L, S = 0, 1, 2
    hls = hls_im.split()
    mask_h = hls[H].point(filter_h)
    mask_l = hls[L].point(filter_l)
    mask_s = hls[S].point(filter_s)

    Mdat = []
    # for debugging:
    #mask_h, mask_l, mask_s = hls_im.split()
    seen = []
    for h, l, s in zip(mask_h.getdata(), mask_l.getdata(), mask_s.getdata()):
        if (h, l, s) not in seen:
            seen.append((h, l, s))
            #print((h, l, s))
        Mdat.append(255 if (h and l and s) else 0)

    mask = mask_h
    mask.putdata(Mdat)

    filtered_im = Image.new("RGB", hls_im.size, color=default_col)
    filtered_im.paste(im, None, mask)
    return filtered_im

