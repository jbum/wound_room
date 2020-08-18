# score_animate.py

import argparse, sys, os, re, glob, time
import configparser
from fpipe import FPipe
from PIL import Image, ImageDraw
import subprocess
# python3 score_animate.py wound_room2.csv

'''


'''


parser = argparse.ArgumentParser(description='Print Star Battles')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no commands are run')
parser.add_argument('-k', '--keep', default=False, action='store_true', help='Keep Temp Tracks')
parser.add_argument('-c', '--config_file', default='wound_room2.cfg', help="Config file to use, default=%(default)s")
parser.add_argument('-o', '--ofile_name', default='untitled.mp4', help='Output file override')
# parser.add_argument('-log', '--log_file_name', help='Optional log file')
parser.add_argument('-rm','--render_mode',type=int,default=0,help='Render Mode (0,1,2)')
# parser.add_argument('-sn', '--sub_noise', default=False, action='store_true', help='Substitute noise')
# parser.add_argument('-fm', '--ffmpeg_instance', default='ffmpeg', help='FFmpeg instance')
# parser.add_argument('-fll', '--ffmpeg_loglevel', default='error', help='FFmpeg loglevel')
parser.add_argument("score_file",help="Score File")
args = parser.parse_args()


st = time.time()

if args.vverbose:
    args.verbose = True

def map_fparam(v,small,large):
    return (large-small)*v/64.0+small

def map_iparam(v,small,large):
    return int(map_fparam(v,small,large)+0.5)

if not os.path.exists(args.config_file):
    print("Config file missing: %s" % (args.config_file))
    sys.exit()

def hsl_to_rgb_color(h,s,v):
    from colorsys import hsv_to_rgb
    r,g,b = hsv_to_rgb(h,s,v)
    return "rgb(%d,%d,%d)" % (int(r*255+0.5),int(g*255+0.5),int(b*255*0.5))

cfg = configparser.ConfigParser()
cfg.read(args.config_file)

cfg_score = cfg['score']

length_seconds = eval(cfg_score['length_seconds'])
nbr_tracks = eval(cfg_score['nbr_tracks'])
track_width_seconds = eval(cfg_score['track_width_seconds'])

clip_noms = list(glob.glob(cfg_score['samples_dir']+"*.wav"))
image_noms = list(glob.glob(cfg_score['images_dir']+"*.jpg")) + list(glob.glob(cfg_score['images_dir']+"*.png"))

frame_height = 1080 # should work properly if I produce 4k output using 2160
frame_width = frame_height*16//9
border_width = frame_width/64.0
track_width = (frame_width-border_width*(nbr_tracks-1))/nbr_tracks # in pixels
track_aspect_ratio = length_seconds / track_width_seconds
track_height = track_aspect_ratio*track_width
total_frames = int(30*length_seconds + 0.5)

time_to_pixelsY = track_height / float(length_seconds)

print("frame_width %d" % (frame_width))
print("track_width = %d" % (track_width))
print("track_height = %d" % (track_height))

# read track info from score file
tracks = [[] for i in range(nbr_tracks)]
with open(args.score_file) as csvfile:
    for line in csvfile:
        if re.match(r'^\s*[\#;]', line):
            continue
        if re.match(r'^\s*[A-Z]', line):
            continue
        if re.match(r'^\s*$', line):
            continue
        tokens = line.split(',')
        track = int(tokens[0])-1
        start,duration,fadein,fadeout = [float(tokens[i]) for i in [1,2,3,4]]
        params = [int(tokens[i]) for i in range(5,5+8)]
        # print("Params: " + str(params))
        tracks[track].append((start,duration,fadein,fadeout,
            params[0],params[1],params[2],params[3],params[4],params[5],params[6],params[7]))


cached_images = {}

def draw_event(fimg,loop_idx,x1,x2,y1,y2,y3,y4):
    global cached_images
    pts = [(x1,y1),(x2,y2),(x2,y4),(x1,y3)]
    if args.render_mode == 0:
        rgbcolor = hsl_to_rgb_color(loop_idx/float(len(clip_noms)),.5,.75)
        draw = ImageDraw.Draw(fimg)
        draw.polygon(pts, fill=rgbcolor)
    elif args.render_mode == 1 or args.render_mode == 2:
        # cache and redraw masks...
        img_nom = image_noms[loop_idx % len(image_noms)]
        mask = Image.new("L",(frame_width, frame_height),'black')
        mdraw = ImageDraw.Draw(mask)
        if args.render_mode == 1:
            mdraw.polygon(pts,fill='white')
        elif args.render_mode == 2:
            cy = frame_height/2
            if y1 > cy or y4 < cy:
                v = 0
            elif y2 > cy: # FADE IN
                r = (cy-y1)/float(y2-y1)
                v = int(r*255)
            elif y3 < cy: # FADE OUT
                r = (y4-cy)/float(y4-y3)
                v = int(r*255)
            else:
                v = 255
            mdraw.rectangle((x1,0,x2,frame_height),fill="rgb(%d,%d,%d)" % (v,v,v))
            # draw a rectangle

        # cache these...
        if loop_idx in cached_images:
            img_src = cached_images[loop_idx]
        else:
            img_src = Image.open(img_nom).resize((frame_width, frame_height), Image.ANTIALIAS)
            cached_images[loop_idx] = img_src

        fimg.paste(img_src, (0,0), mask)

    # resize to be at least as high as event duration, and track-width wide

for frame_nbr in range(total_frames):
    if args.verbose:
        print("Frame %04d / %04d" % (frame_nbr+1,total_frames))
    now_py = frame_nbr * track_height/total_frames # position in absolute pixel coords
    min_py = now_py - frame_height/2 # bounds in absolute pixel coords
    max_py = now_py + frame_height/2
    # create frame image
    frame_img = Image.new("RGB", (frame_width,frame_height), 'black')
    draw = ImageDraw.Draw(frame_img)

    ofst_y = frame_height/2-now_py  # offset such that current time will be at middle of screen
    # print(" ofst = %d" % (ofst_y))


    for track_nbr,track in enumerate(tracks):
        for eidx,event in enumerate(track):
            start_secs,duration,fade_in,fade_out = event[:4]
            params = event[4:]
            loop_idx= map_iparam(params[0],0,len(clip_noms)-1)
            # determine quad coords
            y1 = start_secs * time_to_pixelsY
            y2 = (start_secs + fade_in)*time_to_pixelsY
            y3 = (start_secs+duration-fade_out)*time_to_pixelsY
            y4 = (start_secs+duration)*time_to_pixelsY
            x1 = track_nbr*(track_width+border_width)
            x2 = x1 + track_width
            if y1 <= max_py and y4 >= min_py:
                draw_event(frame_img, loop_idx, x1, x2, ofst_y + y1, ofst_y + y2, ofst_y + y3, ofst_y + y4)

            # draw extra piece for loop...

            if start_secs < length_seconds/2.0:
                start_secs += length_seconds
            else:
                start_secs -= length_seconds

            # determine quad coords
            y1 = start_secs * time_to_pixelsY
            y2 = (start_secs + fade_in)*time_to_pixelsY
            y3 = (start_secs+duration-fade_out)*time_to_pixelsY
            y4 = (start_secs+duration)*time_to_pixelsY
            x1 = track_nbr*(track_width+border_width)
            x2 = x1 + track_width
            if y1 <= max_py and y4 >= min_py:
                draw_event(frame_img, loop_idx, x1, x2, ofst_y + y1, ofst_y + y2, ofst_y + y3, ofst_y + y4)
                # rgbcolor = hsl_to_rgb_color(loop_idx/float(len(clip_noms)),.5,.75)
                # pts = [(x1,ofst_y+y1),(x2,ofst_y+y2),(x2,ofst_y+y4),(x1,ofst_y+y3)]
                # draw.polygon(pts, fill=rgbcolor)

    draw = ImageDraw.Draw(frame_img)
    draw.line([(0,frame_height/2),(frame_width,frame_height/2)],width=2,fill=(255,255,255,127))


    # track is drawn, output frame
    frame_img.save("./frames/f_%04d.png" % (frame_nbr+1))
    if (args.test and frame_nbr >= 100):
        break

# convert to video here...
tmp_video = cfg_score['tmp_video']
src_audio = cfg_score['src_audio']

cmd = '/usr/bin/ffmpeg -r 30 -y -i ./frames/f_%%04d.png -vcodec libx264 -pix_fmt yuv420p -pass 1 -s 1920x1080 -threads 0 -f mp4 %s' % (tmp_video)
subprocess.check_call(cmd, shell=True)
# /usr/bin/ffmpeg -r 30 -y -i ./frames/f_%04d.png -vcodec libx264 -pix_fmt yuv420p -pass 1 -s 1920x1080 -threads 0 -f mp4 untitled.mp4

cmd = 'ffmpeg -i %s -i %s -c copy -map 0:0 -map 1:0 %s' % (tmp_video, src_audio, args.ofile_name)
subprocess.check_call(cmd, shell=True)

print("Wrote to %s, Elapsed = %.1fs" % (args.ofile_name, time.time()-st))

# remove original frames
# cmd = 'rm ./frames/f*.png'
# subprocess.check_call(cmd, shell=True)
'''
Track 0 event 0 fade_in 1.3 fade_out 3.0 y1 = 322, y2 = 351, y3 = 400, y4 = 468
Track 0 event 1 fade_in 3.0 fade_out 3.4 y1 = 400, y2 = 468, y3 = 658, y4 = 736
'''