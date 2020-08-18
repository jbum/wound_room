# construct sample construction score for Wound Room  (outputs EPS)
#
import configparser, argparse, os, sys, datetime, svgwrite
from math import sin
from yarrow import get_hexagram_frange, get_hexagram_irange, get_hexagram

parser = argparse.ArgumentParser(description='Print Star Battles')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-o', '--ofile_name', default='untitled.svg', help='Output file override')
parser.add_argument('-c', '--config_file', default='wound_room.cfg', help="Config file to use, default=%(default)s")
parser.add_argument('-a', '--artistic', default=False, action='store_true', help='Artistic-style rendering')
parser.add_argument('-ns', '--new_style', default=False, action='store_true', help='New Style (normalized params, and more of them)')
args = parser.parse_args()



if not os.path.exists(args.config_file):
    print("Config file missing: %s" % (args.config_file))
    sys.exit()

cfg = configparser.ConfigParser()
cfg.read(args.config_file)

cfg_score = cfg['score']

nbr_tracks = eval(cfg_score['nbr_tracks'])
length_seconds = eval(cfg_score['length_seconds'])
page_width = eval(cfg_score['page_width'])
page_height = eval(cfg_score['page_height'])
seconds_major_mark = eval(cfg_score['seconds_major_mark'])
seconds_minor_mark = eval(cfg_score['seconds_minor_mark'])
cDate = f"{datetime.datetime.now():%Y-%m-%d}"
major_thick = eval(cfg_score['major_thick'])
minor_thick = eval(cfg_score['minor_thick'])

h_margin = eval(cfg_score['h_margin'])
v_margin = eval(cfg_score['v_margin'])
track_pad = eval(cfg_score['track_pad'])
track_height = (page_height - track_pad*(nbr_tracks-1) - v_margin*2) / nbr_tracks
score_width = page_width - (h_margin*2)

def hsl_to_rgb_color(h,s,v):
    from colorsys import hsv_to_rgb
    r,g,b = hsv_to_rgb(h,s,v)
    return "rgb(%d,%d,%d)" % (int(r*255+0.5),int(g*255+0.5),int(b*255*0.5))

def fv(v):
    if abs(v-int(v) < 0.001):
        return "%d" % (v)
    elif abs(v-(int(v)+0.5) < 0.001):
        return "%.1f" % (v)
    else:
        return "%.2f" % (v)


def fill_rect(fd,x1,y1,w,h,clr=None):
    fd.write("q\n")
    fd.write("%.1f %.1f tr\n" % (x1,y1))
    fd.write("newpath\n")
    fd.write("0 0 m %s 0 l %s %s l 0 %s l\n" % (fv(w),fv(w),fv(h),fv(h)))
    fd.write("closepath\n")
    if clr != None:
        fd.write("%s setrgbcolor\n" % (clr))
    fd.write("fill\n")
    fd.write("Q\n")

def do_line(fd,x1,y1,x2,y2):
    fd.write("q\n%s %s m %s %s l S\nQ\n" % (fv(x1),fv(y1),fv(x2),fv(y2)))


svg_document = svgwrite.Drawing(filename = args.ofile_name,
                                size = ("%d" % (page_width), "%d" % (page_height)))

svg_document.add(svg_document.rect(insert = (0, 0),
                                   size = ("%d" % (page_width), "%d" % (page_height)),
                                   stroke = "none",
                                   fill = "white"))


grp = svg_document.g(transform="translate(%d,%d)" % (h_margin,0))




# SCORE BG
bggrp = svg_document.g(fill="black",fill_opacity=".1",stroke="none")
for y in range(nbr_tracks):
    top_y = v_margin + (track_height+track_pad)*y
    bggrp.add(svg_document.rect(insert=(0,top_y),size=(score_width,track_height)))
    # fill_rect(fd, 0, top_y, score_width, -track_height, "0.8 0.8 0.8")

grp.add(bggrp)

# MAJOR TICKS
majgrp = svg_document.g(stroke_width="%.3f" % (major_thick),stroke=cfg_score['major_tick_color'], stroke_linecap="round", stroke_linejoin="round")
# fd.write("%.3f setlinewidth 0.5 0.5 0.5 setrgbcolor\n" % (major_thick))
for majs in range(0, length_seconds + 1):
    if majs % seconds_major_mark != 0:
        continue
    x = majs * score_width/float(length_seconds)
    majgrp.add(svg_document.line(start=(x,0),end=(x, page_height)))


grp.add(majgrp)

# MINOR TICKS
mingrp = svg_document.g(stroke_width="%.3f" % (minor_thick),stroke=cfg_score['minor_tick_color'], stroke_linecap="round", stroke_linejoin="round")
# fd.write("%.3f setlinewidth 0.75 0.75 0.75 setrgbcolor\n" % (minor_thick))
for mins in range(0, length_seconds + 1):
    if mins % seconds_minor_mark != 0 or mins % seconds_major_mark == 0:
        continue
    x = mins * score_width/float(length_seconds)
    mingrp.add(svg_document.line(start=(x,0),end=(x, page_height)))
grp.add(mingrp)

# TIME CAPTIONS
tgrp = svg_document.g(font_family='Helvetica', font_weight='normal', font_size=12, 
                      fill="black", text_anchor='middle', style=cfg_score['label_style'])

# fd.write("/Helvetica findfont\n12 scalefont setfont\n0 0 0 setrgbcolor\n")
text_baseline_y = 16
for majs in range(0, length_seconds + 1):
    if majs % seconds_major_mark != 0:
        continue
    # render text
    x = majs * score_width/float(length_seconds)
    tgrp.add(svg_document.rect(insert=(x-16,text_baseline_y-13),size=(32,17),fill='white'))
    # fill_rect(fd, x-2, text_baseline_y+12, 30, -16, "1 1 1")
    label = "%d:%02d" % (majs/60,majs%60)
    tgrp.add(svg_document.text(label, insert = (x, text_baseline_y)))
    # fd.write("%s %s m\n(%s) show\n" % (fv(x),fv(text_baseline_y),"%d:%02d" % (majs/60,majs%60)))
grp.add(tgrp)

min_sound_length = eval(cfg_score['min_sound_length'])
max_sound_length = eval(cfg_score['max_sound_length'])
min_fade_ratio = eval(cfg_score['min_fade_ratio'])
max_fade_ratio = eval(cfg_score['max_fade_ratio'])

pgrp = svg_document.g(stroke_width=1,stroke='black')
tgrp = svg_document.g(fill='black',font_family='Helvetica', font_weight='bold', font_size=14,text_anchor='middle')

if args.new_style:
    print('Track,"Start","Length","FadeIn",FadeOut","P1","P2","P3","P4","P5","P6","76","P8"')
else:
    print('Track,"Start","Length","FadeOut","P1","P2","P3"')
for y in range(nbr_tracks):
    top_y = v_margin + (track_height+track_pad)*y
    sounds = []
    start = 0
    last_one = False
    while not last_one:
        if length_seconds-start < max_sound_length:
            length = length_seconds-start
            last_one = True
        else:
            length = get_hexagram_frange(min_sound_length,max_sound_length)
        if args.new_style:
            params = [get_hexagram() for i in range(8)] 
        else:
            p1 = get_hexagram_irange(1,32)
            p2 = get_hexagram_irange(1,6)
            p3 = get_hexagram_irange(1,6)
            params = [p1,p2,p3]
        snd = {'start':start,'length':length, 'params':params}
        # print(snd)
        sounds.append(snd)
        start += length
    # add fades and adjust leading/trailing edges
    for i,snd in enumerate(sounds):
        next_snd = sounds[(i+1) % len(sounds)]
        max_overlap = min(snd['length'],next_snd['length'])
        fade_length = get_hexagram_frange(min_fade_ratio, max_fade_ratio) * max_overlap
        snd['fade'] = fade_length
    for i,snd in enumerate(sounds):
        next_snd = sounds[(i+1) % len(sounds)]
        fade_len = snd['fade']
        snd['length'] += fade_len/2
        next_snd['start'] -= fade_len/2
        next_snd['length'] += fade_len/2

    # rotate tracks so the initial cross-fades don't line up.
    rotation_offset = y*length_seconds/4
    for i,snd in enumerate(sounds):
        snd['start'] += rotation_offset
        if snd['start'] > length_seconds:
            snd['start'] -= length_seconds
        if snd['start'] < 0:
            snd['start'] += length_seconds
    sounds = sorted(sounds,key=lambda rec: (rec['start']))


    for i,snd in enumerate(sounds):
        prior_snd = sounds[(i+len(sounds)-1) % len(sounds)]
        fade_in = prior_snd['fade']
        start = snd['start']
        length = snd['length']
        fade_out = snd['fade']
        p1,p2,p3 = snd['params'][:3]
        x1 = start * score_width/float(length_seconds)
        x2 = (start+fade_in) * score_width/float(length_seconds)
        x3 = (start+length-fade_out) * score_width/float(length_seconds)
        x4 = (start+length) * score_width/float(length_seconds)
        y1 = top_y
        y2 = top_y+track_height
        px1,px2,px3,px4 = (x1,x2,x4,x3)
        py1,py2,py3,py4 = (y2,y1,y1,y2)

        rgbcolor = hsl_to_rgb_color(snd['params'][0]/32.0,.5,.75)

        pgrp.add(svg_document.polygon(points=[(px1,py1), (px2,py2), (px3,py3), (px4,py4)],fill=rgbcolor,fill_opacity=0.5))
        if i == 0:
            pgrp.add(svg_document.polygon(points=[(px1+score_width,py1), (px2+score_width,py2), (px3+score_width,py3), (px4+score_width,py4)],fill=rgbcolor,fill_opacity=0.25,stroke_opacity=0.25))
        elif i == len(sounds)-1:            
            pgrp.add(svg_document.polygon(points=[(px1-score_width,py1), (px2-score_width,py2), (px3-score_width,py3), (px4-score_width,py4)],fill=rgbcolor,fill_opacity=0.25,stroke_opacity=0.25))

        for yi,p in enumerate(snd['params']):
            label = "%d" % p
            tgrp.add(svg_document.text(label, insert = ((x2+x3)/2, top_y+14+14*yi)))

    for i,snd in enumerate(sounds):
        start = snd['start']
        length = snd['length']
        fade_out = snd['fade']
        if args.new_style:
            fade_in = sounds[(i+len(sounds)-1) % len(sounds)]['fade']
            p1,p2,p3,p4,p5,p6,p7,p8 = snd['params']
            print("%d,%.2f,%.2f,%.2f,%.2f,%d,%d,%d,%d,%d,%d,%d,%d" % (y+1, start, length, fade_in, fade_out, p1, p2, p3, p4, p5, p6, p7, p8))
        else:
            p1,p2,p3 = snd['params']
            print("%d,%.2f,%.2f,%.2f,%d,%d,%d" % (y+1, start, length, fade_out, p1, p2, p3))



grp.add(pgrp)
grp.add(tgrp)

svg_document.add(grp)
svg_document.save()
if args.verbose:
    print("Wrote to %s" % (args.ofile_name))