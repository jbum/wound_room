# mixing script for Wound Room 2
#
import argparse, sys, os, re, glob, time
import configparser
from fpipe import FPipe

'''
python3 mix_score.py -c wound_room2.cfg wound_room2.csv -o wound_room2.wav -k
1628 ops / 130.31 seconds - original (ffmpeg 4.2.4)
1484 ops / 115.07 seconds - combined some commands
1555 ops / 123.81 seconds - added merge_loop
1556 ops / 62.53 seconds - dev ffmpeg (N-98692-ga5ac819) w/ tremolo

Debug tremolo - appears to be fixed in 4.3.1 (N-98692-ga5ac819) (I was using 4.2.4)


# this produces a serviceable render
# ffmpeg -i wound_room2.wav -codec:a libmp3lame -qscale:a 2 wound_room2_a.mp3


'''

# create src object here and various methods...
# walking thru the code produces an instruction list...
parser = argparse.ArgumentParser(description='Print Star Battles')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no commands are run')
parser.add_argument('-k', '--keep', default=False, action='store_true', help='Keep Temp Tracks')
parser.add_argument('-o', '--ofile_name', default='untitled.wav', help='Output file override')
parser.add_argument('-log', '--log_file_name', help='Optional log file')
parser.add_argument('-c', '--config_file', default='wound_room.cfg', help="Config file to use, default=%(default)s")
parser.add_argument('-a', '--artistic', default=False, action='store_true', help='Artistic-style rendering')
parser.add_argument('-sn', '--sub_noise', default=False, action='store_true', help='Substitute noise')
parser.add_argument('-fm', '--ffmpeg_instance', default='ffmpeg', help='FFmpeg instance')
parser.add_argument('-fll', '--ffmpeg_loglevel', default='error', help='FFmpeg loglevel')
parser.add_argument("score_file",help="Score File")
args = parser.parse_args()


fx = ['', # no effect
      'chorus=0.5:0.9:50|60|40:0.4|0.32|0.3:0.25|0.4|0.3:2|2.3|1.3', # chorus effect
      'aecho=0.8:0.9:1000|1800:0.3|0.25', # big echo
      'aecho=0.8:0.9:1000:0.3', # med echo
      'highpass=<P1 3000-5000>',
      'tremolo=<P1 1-8>:<P2 0.5-1>', # often coredumps in 4.2.4, works in 4.3.1
      'vibrato=<P1 0.5-4>:<P2 0.25-1.0>'
      ] # short echo

st = time.time()

if args.vverbose:
    args.verbose = True

if args.log_file_name:
    with open(args.log_file_name,"w") as logfile:
        logfile.write("# Commands produced by mix_score.py")

def map_fparam(v,small,large):
    return (large-small)*v/64.0+small

def map_iparam(v,small,large):
    return int(map_fparam(v,small,large)+0.5)


if not os.path.exists(args.config_file):
    print("Config file missing: %s" % (args.config_file))
    sys.exit()

cfg = configparser.ConfigParser()
cfg.read(args.config_file)

cfg_score = cfg['score']

if 'ffmpeg_instance' in cfg_score:
    args.ffmpeg_instance = cfg_score['ffmpeg_instance']

length_seconds = eval(cfg_score['length_seconds'])
nbr_tracks = eval(cfg_score['nbr_tracks'])
clip_noms = []
for nom in glob.glob(cfg_score['samples_dir']+"*.wav"):
    if args.sub_noise:
        clip_noms.append("./tests/test_noise.wav")
    else:
        clip_noms.append(nom)
if args.verbose:
    print("Got %d clips" % (len(clip_noms)))

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
        # print(params)

fpipe = FPipe("WR", args)

for tidx,track in enumerate(tracks):
    max_length = max([event[0]+event[1] for event in track])

    fpipe.push()
    for eidx,event in enumerate(track):
        start,dst_length,fade_in,fade_out = event[:4]
        params = event[4:]
        # fpipe = FPipe("T%02d%02d" % (tidx,eidx),args)
        src_loop_index, speed, effect, effect_p1, effect_p2, src_loop_length, rotation, loop_offset_ratio = (
                map_iparam(params[0],0,len(clip_noms)-1),
                [-2,-1,-0.5,0.5,1,2][map_iparam(params[1],0,5)],
                map_iparam(params[2],0, len(fx)-1),
                map_fparam(params[3],0, 1),
                map_fparam(params[4],0, 1),
                map_fparam(params[5],float(cfg_score['min_src_loop_length']),float(cfg_score['max_src_loop_length'])),
                map_fparam(params[6],0,1),
                map_fparam(params[7],0,1) )

        src_fname = clip_noms[src_loop_index]

        # extract sub-sample, rotate it, reverse it, set its speed and loop it to desired length
        fpipe.open(src_fname)
        D,SR,CH = fpipe.get_wav_info()
        if src_loop_length < D:
            random_start = loop_offset_ratio*(D-src_loop_length)
            fpipe.crop(random_start,src_loop_length)
        D,SR,CH = fpipe.get_wav_info()
        fpipe.rotate(rotation) # randomly rotate loop
        if speed < 0:
            fpipe.reverse()
        if abs(speed) != 1:
            fpipe.changespeed(abs(speed))
        D,SR,CH = fpipe.get_wav_info()
        repetitions = 1 + dst_length//D
        fpipe.loop(repetitions)
        fpipe.crop(0,dst_length)

        # apply fx
        fx_str = fx[effect]
        if fx_str != '' and fx_str != None:
            fpipe.fx(fx_str, effect_p1, effect_p2)

        # trim if needed
        D,SR,CH = fpipe.get_wav_info()
        if D != dst_length:
            fpipe.crop(0, dst_length)

        # add fades
        fpipe.fade_in_out(fade_in, fade_out)

        # position at debut time
        fpipe.prepend_silence(start)

        # pad to desired whole loop length
        D,SR,CH = fpipe.get_wav_info()
        fpipe.pad(max(D,max_length))

        fpipe.collect()

        # tracklist.append(fpipe.lfile)
        # optional

    # mix each clip at it's start time to composite track
    fpipe.merge()
    fpipe.merge_loop(length_seconds)
    fpipe.pop()
    fpipe.collect()


# mix n tracks with desired panning
fpipe.merge()
fpipe.earwax()
fpipe.save(args.ofile_name)

if not args.keep:
    fpipe.clean_up()

print("Saved to " + args.ofile_name)
print("Elapsed %.2f secs, %d ops" % (time.time() - st, fpipe.cnbr))




'''
First successful pass, 85 seconds.
'''