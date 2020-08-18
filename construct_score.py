# construct sample construction score for Wound Room  (outputs EPS)
#
import configparser, argparse, os, sys, datetime
from yarrow import get_hexagram

parser = argparse.ArgumentParser(description='Print Star Battles')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-o', '--ofile_name', default='untitled.eps', help='Output file override')
parser.add_argument('-c', '--config_file', default='wound_room.cfg', help="Config file to use, default=%(default)s")
parser.add_argument('-a', '--artistic', default=False, action='store_true', help='Artistic-style rendering')
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


with open(args.ofile_name,"w") as fd:
    fd.write("""%%!PS-Adobe-3.0 EPSF-3.0
%%%%BoundingBox: 0 0 %d %d
%%%%Creator: Jim Bumgardner (Krazydad.com)
%%%%Title: Star Battle Puzzle
%%%%Creation Date: %s
%%%% Initialization:
/m {moveto} bind def
/l {lineto} bind def
/c {curveto} bind def
/tr {translate} bind def
/sc {scale} bind def
/S {stroke} bind def
/q {gsave} bind def
/Q {grestore} bind def
""" % (page_width,page_height,cDate))

    fill_rect(fd, 0, 0, page_width, -page_height, "1 1 1")
    fd.write("q\n")
    fd.write("%s %s tr\n" % (fv(h_margin), fv(0)))


    # SCORE BG
    for y in range(4):
    	top_y = page_height - (v_margin + (track_height+track_pad)*y)
    	fill_rect(fd, 0, top_y, score_width, -track_height, "0.8 0.8 0.8")

    # MAJOR TICKS
    fd.write("%.3f setlinewidth 0.5 0.5 0.5 setrgbcolor\n" % (major_thick))
    for majs in range(0, length_seconds + 1):
    	if majs % seconds_major_mark != 0:
    		continue
    	x = majs * score_width/float(length_seconds)
    	do_line(fd, x, 0, x, page_height)

    # MINOR TICKS
    fd.write("%.3f setlinewidth 0.75 0.75 0.75 setrgbcolor\n" % (minor_thick))
    for mins in range(0, length_seconds + 1):
    	if mins % seconds_minor_mark != 0 or mins % seconds_major_mark == 0:
    		continue
    	x = mins * score_width/float(length_seconds)
    	do_line(fd, x, 0, x, page_height)

    # TIME CAPTIONS
    fd.write("/Helvetica findfont\n12 scalefont setfont\n0 0 0 setrgbcolor\n")
    text_baseline_y = page_height-16
    for majs in range(0, length_seconds + 1):
    	if majs % seconds_major_mark != 0:
    		continue
    	# render text
    	x = majs * score_width/float(length_seconds) - 12
    	fill_rect(fd, x-2, text_baseline_y+12, 30, -16, "1 1 1")
    	fd.write("%s %s m\n(%s) show\n" % (fv(x),fv(text_baseline_y),"%d:%02d" % (majs/60,majs%60)))


    fd.write("Q\n")


print("Wrote to %s" % (args.ofile_name))