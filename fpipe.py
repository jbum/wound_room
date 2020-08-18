# fpipe (pipeline object for ffmpeg)
import subprocess
import random
import sys

class FPipe:
    def __init__(self, prefix=None,args={}):
        if prefix != None:
            self.prefix = prefix
        else:
            self.prefix = "TMP"
        rand_str = ''.join([chr(ord('A')+random.randint(0,25)) for i in range(3)])
        self.prefix = "./tmp/" + self.prefix + "_" + rand_str + "_"
        self.commands = []
        self.cnbr = 0
        self.lfile = "<UNKNOWN>"
        self.args = args
        self.stack = []
        self.merge_collection = []
        self.ffmpeg_instance = self.args.ffmpeg_instance
        self.ffmpeg_loglevel = self.args.ffmpeg_loglevel
        self.log("# initialize %s" % (self.prefix))

    def log(self, msg, append=True):
        if self.args.verbose or self.args.test:
            print("->" + msg)
        if self.args.log_file_name:
            with open(self.args.log_file_name,"a" if append else "w") as logfile:
                logfile.write(msg + "\n")

    def do_command(self, cmd):
        self.log(cmd)
        if not self.args.test:
            subprocess.check_call(cmd, shell=True)

    def issue_cmd(self,cmd): # usually used once per function, although I've used it multiple on some...
        cfile = "%s%04d.wav" % (self.prefix, self.cnbr)
        cmd = cmd.replace("<FFMPEG>","%s -y -hide_banner -loglevel %s -nostats -ac 2" % (self.ffmpeg_instance, self.ffmpeg_loglevel))
        cmd = cmd.replace("<LNAME>",self.lfile)
        cmd = cmd.replace("<CNAME>",cfile)
        self.do_command(cmd)
        self.cnbr += 1
        self.lfile = cfile

    def clean_up(self):
        self.do_command("rm %s*.wav" % (self.prefix))
        return self

    def open(self,fname):
        self.log("# open")
        cmd = "cp %s <CNAME>" % (fname)
        self.issue_cmd(cmd)
        return self

    def save(self, oname):
        self.log("# save")
        if '.mp3' in oname:
            cmd = '<FFMPEG> -i <LNAME> -codec:a libmp3lame -qscale:a 2 %s' % (oname)
        else:
            cmd = "cp <LNAME> %s" % (oname)
        self.issue_cmd(cmd)
        return self

    def collect(self):
        self.merge_collection.append(self.lfile)
        return self

    def push(self):
        self.stack.append({'mc':list(self.merge_collection)})
        self.merge_collection = []
        return self

    def pop(self):
        if len(self.stack) == 0:
            print("ERROR: unbalanced pop")
            sys.exit(1)
        sframe = self.stack.pop()
        self.merge_collection = sframe['mc']
        return self


    def catenate(self, file1, file2):
        self.log("# catenate")
        cmd = "<FFMPEG> -i %s -i %s -filter_complex '[0:0][1:0]concat=n=2:v=0:a=1[out]' -map '[out]' <CNAME>" % (file1, file2)
        # attempt to do all in one
        #        ffmpeg -i test_noise.wav -filter_complex "[0]atrim=0:duration=2[v0];[0]atrim=2:duration=1[v1];[v0][v1]concat=n=2:v=0:a=1[out]" -map "[out]" test1.wav
        self.issue_cmd(cmd)
        return self

    # get useful info from WAV header
    def get_wav_info(self): # retrieve info for current self.lfile
        import os, struct
        path = self.lfile
        with open(path,'rb') as f:
            a = f.read(36)
            (chunkID,chunkSize,fmt,
              subChunk1ID,subChunk1Size,
                audioFmt,numChannels,sampleRate,byteRate,blockAlign,bitsPerSample) = struct.unpack("<4sLL4sLHHLLHH",a)
            while True:
                a = f.read(8)
                (subchunkID, subChunkSize) = struct.unpack("<4sL",a)
                if subchunkID == b'data':
                    dataSize = subChunkSize
                    break
                else:
                    if self.args.vverbose:
                      print("Skipping %s" % (subchunkID))
                    f.seek(subChunkSize,1)
        duration = dataSize / float(byteRate)
        if self.args.verbose:
            print("Got WAV info: dur=%.2f SR=%d channels=%d" % (duration,sampleRate,numChannels))
        return duration, sampleRate, numChannels

    def crop(self, start=0, duration=1):
        self.log("# crop start=%.2f dur=%.2f" % (start,duration))
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af 'atrim=%.3f:duration=%.3f' <CNAME>" % (start, duration)
        self.issue_cmd(cmd)
        return self
        # cmd = "<FFMPEG> -i test_noise.wav -af 'afade=t=in:st=0:d=2,afade=t=out:st=2:d=2' test3.wav"
        # ffmpeg -y -hide_banner -loglevel warning -nostats -ac 2 -guess_layout_max 1 -i ./tmp/MT0_VIQ_0000.wav 
        # -af 'atrim=210.000:duration=15.380' ./tmp/MT0_VIQ_0001.wav

    def rotate(self, ratio):
        self.log("# rotate %.2f%%" % (ratio*100))
        D,SR,CH = self.get_wav_info()
        rotate_point = ratio*D
        if rotate_point > 0.001:

            cmd = "<FFMPEG> -i <LNAME> -filter_complex '[0]atrim=%.3f:duration=%.3f[a0];[0]atrim=0:duration=%.3f[a1];[a0][a1]concat=2:v=0:a=1[out]' -map '[out]' <CNAME>" % (
                rotate_point,D-rotate_point,rotate_point
                )
            self.issue_cmd(cmd)

        return self
        # clip_name = self.lfile
        # clip_name_a = clip_name.replace(".wav","_a.wav")
        # clip_name_b = clip_name.replace(".wav","_b.wav")
        # cmd = "<FFMPEG> -i %s -af 'atrim=0:duration=%.3f' %s" % (clip_name, rotate_point, clip_name_a)
        # self.issue_cmd(cmd)
        # cmd = "<FFMPEG> -i %s -af 'atrim=%.3f:duration=%.3f' %s" % (clip_name, rotate_point, D-rotate_point,clip_name_b)
        # self.issue_cmd(cmd)
        # # catenate
        # self.catenate(clip_name_a, clip_name_b)

    def reverse(self):
        self.log("# reverse")
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af areverse <CNAME>"
        self.issue_cmd(cmd)
        return self

    def fx(self, fx_str, p1, p2):
        import re
        self.log("# fx %s" % (fx_str))
        pat = re.compile(r"<P(\d) (.*?)-(.*?)>")
        pratios = [p1, p2]
        params = [0,0]
        m = pat.search(fx_str)
        while m:
            pidx, low, high = (int(m.group(1))-1, float(m.group(2)), float(m.group(3)))
            v = pratios[pidx]*(high-low)+low
            fx_str = fx_str.replace(m.group(0),"%.1f" % v) # tremolo crashes if I use .3f
            m = pat.search(fx_str)
        self.log("# fx translated: %s" % (fx_str))
        # compute p1, p2 using ranges in fx_str
        # substitute <Pn low-hi> with computed p1
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af '%s' <CNAME>" % (fx_str)
        self.issue_cmd(cmd)
        return self


    def earwax(self):
        # makes nicer to listen to on headphones
        self.log("# earwax")
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af earwax <CNAME>"
        self.issue_cmd(cmd)
        return self

    def changespeed(self, speed):
        # ffmpeg -i test_bach.wav -filter_complex "[0]asetrate=22050,aresample=44100[out]" -map "[out]" testC.wav
        # ffmpeg -i test_bach.wav -af "asetrate=22050,aresample=44100" testD.wav

        self.log("# changespeed %.2fX" % (speed))
        D,SR,CH = self.get_wav_info() # 2 = 88k  1/2 = 22k
        if speed != 1:
            # cmd = "<FFMPEG> -i <LNAME> -af asetrate=%d <CNAME>" % (SR*speed)
            # self.issue_cmd(cmd)
            # # resample at original rate to ease future mixing
            # cmd = "<FFMPEG> -i <LNAME> -af aresample=%d <CNAME>" % (SR)
            # self.issue_cmd(cmd)
            cmd = "<FFMPEG> -i <LNAME> -af asetrate=%d,aresample=%d <CNAME>" % (SR*speed,SR)
            self.issue_cmd(cmd)
        return self

    # ?? optimize?
    def prepend_silence(self, amt):
        self.log("# prepend_silence %.2f secs silence" % (amt))
        D,SR,CH = self.get_wav_info()
        s_name = self.lfile.replace(".wav","_s.wav")
        t_name = self.lfile
        amtMS = int(amt*1000)
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af 'adelay=%d|%d' <CNAME>" % (amtMS,amtMS)
        self.issue_cmd(cmd)
        return self

    def pad(self, desired_len):
        self.log("# pad to %.2f secs" % (desired_len))
        D,SR,CH = self.get_wav_info()
        if desired_len > D:
            cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af 'apad=whole_dur=%.3f' <CNAME>" % (desired_len)
            self.issue_cmd(cmd)
        return self
   
    def loop(self, repetitions): # including src
        self.log("# loop %d repetitions" % (repetitions-1))
        D,SR,CH = self.get_wav_info()
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af 'aloop=%d:size=%d' <CNAME>" % (repetitions-1, SR * D)
        self.issue_cmd(cmd)
        return self

    def fade_in_out(self, fade_in_dur, fade_out_dur):
        # self.fade_in(fade_in_dur)
        # self.fade_out(fade_out_dur)
        self.log("# fade in=%.3f out=%.3f" % (fade_in_dur, fade_out_dur))
        D,SR,CH = self.get_wav_info()
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af 'afade=t=in:st=0:d=%.3f,afade=t=out:st=%.3f:d=%.3f' <CNAME>" % (fade_in_dur, D-fade_out_dur, fade_out_dur)
        self.issue_cmd(cmd)
        return self

    def fade_in(self, fade_in_dur):
        self.log("# fade in=%.3f" % (fade_in_dur))
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af 'afade=t=in:st=0:d=%.3f' <CNAME>" % (fade_in_dur)
        self.issue_cmd(cmd)
        return self

    def fade_out(self, fade_out_dur):
        self.log("# fade out=%.3f" % (fade_out_dur))
        D,SR,CH = self.get_wav_info()
        cmd = "<FFMPEG> -guess_layout_max 1 -i <LNAME> -af 'afade=t=out:st=%.3f:d=%.3f' <CNAME>" % (D-fade_out_dur, fade_out_dur)
        self.issue_cmd(cmd)
        return self

    def mix(self, panlist = None): # !! unused
        self.log("# mix")
        N = len(self.merge_collection)
        cum = sum(range(1,N+1))
        cmd = "<FFMPEG> %s -filter_complex 'amix=inputs=%d:duration=longest:weights=%s' <CNAME>" % (
             ' '.join(["-i "+fname for fname in self.merge_collection]), N,' '.join(["%.4f" % ((N-i)/float(cum)) for i in range(len(self.merge_collection))]))
        self.issue_cmd(cmd)
        return self


    def merge(self, pans=None): # !! pans unused
        self.log("# merge")
        N = len(self.merge_collection)
        cum = sum(range(1,N+1))
        inputstr = ' '.join(["-i "+fname for fname in self.merge_collection])
        chanstr = ''.join(["[%d:a]" % (i) for i in range(N)])
        # use = instead of < to avoid renormalization
        panLstr = 'c0=' + ('+'.join(["c%d" % (i*2) for i in range(N)]))
        panRstr = 'c1=' + ('+'.join(["c%d" % (i*2+1) for i in range(N)]))
        cmd = "<FFMPEG> %s -filter_complex '%samerge=inputs=%d,pan=stereo|%s|%s[a]' -map '[a]'  <CNAME>" % (
             inputstr, chanstr, N, panLstr, panRstr)
        self.issue_cmd(cmd)
        return self

    # mixes excess tail of loop into front of loop and truncates
    def merge_loop(self, loop_point):
        self.log("# merge_loop dur=%.3f" % (loop_point))
        D,SR,CH = self.get_wav_info()
        if D > loop_point:
            remainder = D - loop_point
            ofile = self.lfile
            # extract it out to temp file
            self.push() \
                 .crop(loop_point, remainder).pad(loop_point).collect() \
                 .open(ofile).crop(0, loop_point).collect() \
                 .merge() \
                 .pop()
        else:
            self.log("# Skipping merge_loop, D=%.2f" % (D))
        return self

