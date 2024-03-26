from exptools2.core import Session
from StopStimulus import StopStimulus, FixationCircle, StopCircle
from StopTrial import StopSignalTrial, AllInstructions, OperatorScreen #ShowInstructions, mainInstructions, practiceInstructions, WaitInstructions, TestSoundTrial
from psychopy import visual, data
import datetime
import glob
import pandas as pd
import numpy as np
import os
import os.path as op
import subprocess
import wave
from scipy.io import wavfile
import copy
import pickle as pkl
import sys
import matplotlib.pyplot as plt

class StopSignalSession(Session):

    def __init__(self, output_str, output_dir, settings_file, subject_initials, tr, start_block, gend, age, session_nr):
        super(StopSignalSession, self).__init__(output_str=output_str,
                                                output_dir=output_dir,
                                                settings_file=settings_file)

        self.subject_initials=subject_initials
        self.gend=gend
        self.age=age
        self.start_block = int(start_block)  # allows for starting at a later block than 1
        self.design=None
        self.tr = tr
        self.session_nr = session_nr
        self.test_sound_button = self.settings['input']['test_sound_button']     # define button to test sound
        self.line_space = self.settings['stimulus']['line_space']            # define amount of line spacing between instruction texts
        self.operator_button = self.settings['input']['operator_skip_button']
        self.ev_to_start = 0

        # if self.settings['preferences']['general']['audioEng'] == 'psychopy':
            # # BEFORE moving on, ensure that the correct audio driver is selected
            # from psychopy import prefs
            # prefs.general['audioLib'] = self.settings['preferences']['general']['audioLib']

            # from psychopy.sound import Sound
            # from psychopy.sound.backend_sounddevice import SoundDeviceSound       

        self.response_button_signs = [self.settings['input']['response_button_left'],
                                      self.settings['input']['response_button_right']]

        self.phase_durations = np.array([1000,  # phase 0: wait for scan pulse
                                         0.5,  # phase 1: fixation circle
                                         2,    # phase 2: stimulus
                                         0.5,  # phase 3: feedback (practice session only)
                                         3])   # phase 4: ITI
                                         
        self.phase_names = ['fix_circ_1', 
                            'stimulus', 
                            'feedback',
                            'fic_circ_2']

    # creating a mixture class would be a lot nicer but I can't be bothered so I'll cheat and include everything
    # here
    # def setup_sound_system(self):
    #     """initialize pyaudio backend, and create dictionary of sounds."""
    #     self.pyaudio = pyaudio.PyAudio()
    #     self.sound_files = \
    #     subprocess.Popen('ls ' + os.path.join('.', 'sounds', '*.wav'), shell=True,
    #                      stdout=subprocess.PIPE).communicate()[0].split('\n')[0:-1]
    #     self.sounds = {}
    #     for sf in self.sound_files:
    #         self.read_sound_file(file_name=sf)
    #         # print self.sounds

    # def read_sound_file(self, file_name, sound_name=None):
    #     """Read sound file from file_name, and append to self.sounds with name as key"""
    #     if sound_name == None:
    #         sound_name = os.path.splitext(os.path.split(file_name)[-1])[0]

    #     rate, data = wavfile.read(file_name)
    #     # create stream data assuming 2 channels, i.e. stereo data, and use np.float32 data format
    #     stream_data = data.astype(np.int16)

    #     # check data formats - is this stereo sound? If so, we need to fix it.
    #     wf = wave.open(file_name, 'rb')
    #     # print sound_name
    #     # print wf.getframerate(), wf.getnframes(), wf.getsampwidth(), wf.getnchannels()
    #     if wf.getnchannels() == 2:
    #         stream_data = stream_data[::2]

    #     self.sounds.update({sound_name: stream_data})

    #def play_bleep(self):

    #    self.bleeper.play()

    def load_design(self):

        fn = 'sub-' + str(self.subject_initials).zfill(3) + '_ses-' + str(self.session_nr) + '_tr-' + str(self.tr) + '_design_task-SST'
        design = pd.read_csv(os.path.join('designs_SST', fn + '.csv'), sep='\t', index_col=False, na_values=['nan','NaN'])

        self.design = design
        #print(self.design.direction)
        #self.design = self.design.apply(pd.to_numeric)  # cast all to numeric

    def prepare_staircase(self):
        # TODO: load from previous run?

        # check for old file
        now = datetime.datetime.now()
        opfn = now.strftime("%Y%m%d")
        expected_filename = 'sub-' + str(self.subject_initials).zfill(3) + '_ses-' + str(self.session_nr) + '_tr-' + str(self.tr) + '_task-SST' + '_' + opfn
        fns = glob.glob('./data_SST/' + expected_filename + '-*_block-*staircase.pkl')

        if self.start_block > 1 and len(fns) == 1:
            # if previous run was created
            with open(fns[0], 'rb') as f:
                print("You are attempting to use a previous staircase: " + str(fns))
                self.stairs = pkl.load(f)
                print('loading of previous staircase successful')

        else:
            # Make dict
            info = {'startPoints': [.200]}  # start points for the one staircase

            # create staircases
            self.stairs = []
            for thisStart in info['startPoints']:
                # we need a COPY of the info for each staircase
                # (or the changes here will be made to all the other staircases)
                thisInfo = copy.copy(info)

                # now add any specific info for this staircase
                thisInfo['thisStart'] = thisStart  # we might want to keep track of this
                thisStair = data.StairHandler(startVal=thisStart,
                                              nReversals=None,
                                              nUp=1,
                                              nDown=1,
                                              extraInfo=thisInfo,
                                              stepType='lin',
                                              minVal=0.050,
                                              nTrials=1000,
                                              maxVal=0.900,
                                              stepSizes=[0.050])
                self.stairs.append(thisStair)

            # Save staircases
            # with open(self.output_dir + '/' + str(self.subject_initials) + '_' + str(self.tr) + '_' + str(opfn) + '_staircases.pkl', 'wb') as f:
            #with open(self.output_dir + '/' + self.output_str + '_staircases.pkl', 'wb') as f:    
            #    pkl.dump(self.stairs, f)

        self.design.staircase_ID = -1
        for block in np.unique(self.design.block):
            if block < self.start_block:
                continue

            # how many stop trials this block?
            n_stop_trials = self.design.loc[self.design.block == block].stop_trial.sum()

            staircase_idx = np.tile(np.arange(len(self.stairs)), reps=1000)[:int(n_stop_trials)]
            #np.random.shuffle(staircase_idx) # only works if multiple staircases

            # append to design
            self.design.loc[(self.design.stop_trial == 1) & (self.design.block == block), 'staircase_id'] = \
                staircase_idx
            
            self.design.loc[(self.design.stop_trial == 1) & (self.design.block == block), 'staircase_start_val'] = \
                self.stairs[0].extraInfo['thisStart']
                #info['startPoints']

            #print(self.design)

    def prepare_objects(self):
        #config = self.config

        self.left_stim = StopStimulus(win=self.win, direction=0,
                                      arrow_size_horizontal_degrees=self.settings['stimulus']['arrow_size'])

        self.right_stim = StopStimulus(win=self.win, direction=1,
                                       arrow_size_horizontal_degrees=self.settings['stimulus']['arrow_size'])
                                       
        self.fixation_circle = FixationCircle(win=self.win,
                                              circle_radius_degrees=self.settings['stimulus']['circle_radius_degrees'],
                                              line_width=self.settings['stimulus']['line_width'],
                                              line_color=self.settings['stimulus']['line_color'])

        self.stop_circle = FixationCircle(win=self.win,
                                          circle_radius_degrees=self.settings['stimulus']['circle_radius_degrees'],
                                          line_width=self.settings['stimulus']['line_width'],
                                          line_color=self.settings['stimulus']['stop_line_color'])

    def save_data(self, block_nr=None):

        global_log = pd.DataFrame(self.global_log).set_index('trial_nr').copy()
        global_log['onset_abs'] = global_log['onset'] + self.exp_start

        # Only non-responses have a duration
        nonresp_idx = ~global_log.event_type.isin(['response', 'trigger', 'pulse', 'non_response_keypress'])
        last_phase_onset = global_log.loc[nonresp_idx, 'onset'].iloc[-1]

        if block_nr is None:
            dur_last_phase = self.exp_stop - last_phase_onset
        else:
            dur_last_phase = self.clock.getTime() - last_phase_onset
        durations = np.append(global_log.loc[nonresp_idx, 'onset'].diff().values[1:], dur_last_phase)
        global_log.loc[nonresp_idx, 'duration'] = durations

        # Same for nr frames
        nr_frames = np.append(global_log.loc[nonresp_idx, 'nr_frames'].values[1:], self.nr_frames)
        #print(nr_frames)
        global_log.loc[nonresp_idx, 'nr_frames'] = nr_frames.astype(int)

        # Round for readability and save to disk
        global_log = global_log.round({'onset': 5, 'onset_abs': 5, 'duration': 5})

        global_log['gender'] = self.gend
        global_log['age'] = self.age
        global_log['session'] = self.session_nr

        if block_nr is None:
            f_out = op.join(self.output_dir, self.output_str + '_events.tsv')
        else:
            f_out = op.join(self.output_dir, self.output_str + '_block-' + str(block_nr) + '_events.tsv')
        global_log.to_csv(f_out, sep='\t', index=True)

        # Save frame intervals to file
        self.win.saveFrameIntervals(fileName=f_out.replace('_events.tsv', '_frameintervals.log'), clear=False)

        # save pickle for staircase
        if block_nr is not None:
            with open(self.output_dir + '/' + self.output_str + '_block-' + str(block_nr) + '_staircase.pkl', 'wb') as f:    
                pkl.dump(self.stairs, f)

        #if block_nr is not None:
        #    pkl_out = open(op.join(self.output_dir, self.output_str + '_block-' + str(block_nr) + 'staircase.pkl'), "wb")
        #    pkl.dump(self.stairs, pkl_out)
        #    pkl_out.close()

    def close(self):
        """ 'Closes' experiment. Should always be called, even when
        experiment is quit manually (saves onsets to file). """

        if self.closed:  # already closed!
            return None

        # self.win.saveMovieFrames(fileName='frames/DEMO2.png')

        self.win.callOnFlip(self._set_exp_stop)
        self.win.flip()
        self.win.recordFrameIntervals = False

        print(f"\nDuration experiment: {self.exp_stop:.3f}\n")

        if not op.isdir(self.output_dir):
            os.makedirS(self.output_dir)

        self.save_data()

        # Create figure with frametimes (to check for dropped frames)
        # fig, ax = plt.subplots(figsize=(15, 5))
        # ax.plot(self.win.frameIntervals)
        # ax.axhline(1. / self.actual_framerate, c='r')
        # ax.axhline(1. / self.actual_framerate + 1. / self.actual_framerate, c='r', ls='--')
        # ax.set(xlim=(0, len(self.win.frameIntervals) + 1), xlabel='Frame nr', ylabel='Interval (sec.)',
        #        ylim=(-0.1, 0.5))
        # fig.savefig(op.join(self.output_dir, self.output_str + '_frames.png'))

        if self.mri_simulator is not None:
            self.mri_simulator.stop()

        self.win.close()
        self.closed = True
        
#     def process_data(self, data, make_plot=False):
#         data['onset'] = data['onset'] - data.loc[data['event_type']=='pulse','onset'].values[0]
#         data = data.loc[(data.event_type!='pulse')]         # remove pulses
#         data = data.loc[~pd.isnull(data['trial_nr'])]       # remove stuff without trial numbers
#         data = data.loc[data.event_type.isin(['stimulus', 'response'])]  # only stim & responses
#         data = data.loc[(data.null_trial == 0)]             # remove null trials
#         data = data.loc[(data.phase == 1)]                  # Only include responses given in phase 1
# 
#         ## find trials with responses
#         has_response = data.groupby('trial_nr')['choice_key'].apply(lambda x: np.any(pd.notnull(x)))
#         has_response.name = 'has_response'
# 
#         data = pd.merge(data, has_response, left_on='trial_nr', right_index=True)  # merge back in
# 
#         # categorize fs / ss /go
#         data['trial_type'] = np.nan
#         data.loc[(data['stopsig_trial'] == 1) & (data['has_response'] == 1) , 'trial_type'] = 'fs'
#         data.loc[(data['stopsig_trial'] == 1) & (data['has_response'] == 0), 'trial_type'] = 'ss'
#         data.loc[(data['stopsig_trial'] == 0), 'trial_type'] = 'go'
# 
#         # categorize response left / response right
#         data = pd.merge(data, data.loc[data.event_type=='response', ['trial_nr', 'rt']], on='trial_nr', how='outer')
#         data.loc[(data['event_type'] == 'response') & (data.response == 'c'), 'trial_type'] = 'response_right'
#         data.loc[(data['event_type'] == 'response') & (data.response == 'b'), 'trial_type'] = 'response_left'
#     
#         # look at staircase of behavioural data
#         if make_plot:
#             tmp = data.loc[data['current_ssd']>0, ['trial_nr', 'staircase_id', 'current_ssd']]
#             plt.plot(np.arange(tmp.shape[0]), tmp['current_ssd'])
#             plt.xlabel('Trial')
#             plt.ylabel('SSD')
#             
#         print('Number of failed stops: ' + str(len(data.trial_type.loc[data.trial_type=='fs'])))
#         print('Number of successful stops: ' + str(len(data.trial_type.loc[data.trial_type=='ss'])))
#             
#         return data

    # creates the trials at the start to save computatinoal resources throughout exp
    # BUT, need to update the SSD after each stop trial so cannot add them at the start
    def create_trials(self, block_nr):

        this_block_design = self.design.loc[self.design.block == block_nr]

        self.trials = []

        for index, row in this_block_design.iterrows():

            this_trial_parameters = {'trial_nr': row['trial_ID'],
                                        'direction': row['direction'],
                                        'stopsig_trial': row['stop_trial'],
                                        'jitter': row['jitter'],
                                        'block_nr': block_nr,
                                        'subject': row['subject'],
                                        'current_ssd': 0.2,
                                        'staircase_id': row['staircase_id'],
                                        'staircase_start_val': row['staircase_start_val'],
                                        'n_trs': row['n_trs'],
                                        'null_trial': row['null_trial']}

            phase_durations = [row['jitter'],
                               row['stimulus_dur'],
                               row['feedback_dur'],
                               100]   # show fixation cross 5 until scanner sync!

            self.trials.append(StopSignalTrial(trial_nr=int(index),
                                             #ID=self.subject_initials,
                                             parameters=this_trial_parameters,
                                             phase_durations=phase_durations,
                                             phase_names=self.phase_names,
                                             session=self))

    def run(self):
        """ Runs this Stop Signal task"""    

        self.load_design()
        self.prepare_staircase()
        self.prepare_objects()

        trial_nr = None

        if self.exp_start is None:
            self.start_experiment()

        if self.subject_initials.startswith('p'): # if practice task

            # You will now start practice task
            instructions_practice = AllInstructions(trial_nr,ID=-1, parameters={}, phase_durations=[10000], session=self, win=self.win, instruct_num=3)
            instructions_practice.run()

            # Show instructions for the task
            instructions_show = AllInstructions(trial_nr,ID=-1, parameters={}, phase_durations=[10000], session=self, win=self.win, instruct_num=2)
            instructions_show.run()
            
            # Show second set of instructions for the task
            instructions_show = AllInstructions(trial_nr,ID=-1, parameters={}, phase_durations=[10000], session=self, win=self.win, instruct_num=6)
            instructions_show.run()

        else: # if main task

            print('waiting for operator screen')
            # you will now start the main task
            # instructions_main = AllInstructions(trial_nr,ID=-1, parameters={}, phase_durations=[10000], session=self, win=self.win, instruct_num=4)
            # instructions_main.run()

        #soundy = TestSoundTrial(trial_nr,ID=1, parameters={}, phase_durations=[10000], session=self, win=self.win)
        #soundy.run()

        # warn participant the task is about to task
        #instructions_ready = AllInstructions(trial_nr,ID=-1, parameters={}, phase_durations=[5], session=self, win=self.win, instruct_num=5)
        #instructions_ready.run()

        all_blocks = np.unique(self.design.block)
                
        for block_nr in all_blocks:

            if block_nr < self.start_block:
                continue

            self.create_trials(block_nr)

            self.ev_to_start = 0

            instructions_operator = OperatorScreen(trial_nr,ID=-1, parameters={}, phase_durations=[10000], session=self, win=self.win)
            instructions_operator.run()

            print('waiting for scanner screen')

            instructions_wait = AllInstructions(trial_nr,ID=-1, parameters={}, phase_durations=[10000], session=self, win=self.win, instruct_num=1)
            instructions_wait.run()

            # loop over trials
            for trial in self.trials:

                if trial.parameters['stopsig_trial'] == 1.0:
                    #this_trial_staircase_id = int(trial.parameters['staircase_id'])
                    this_trial_staircase_id = 0
                    this_trial_ssd = next(self.stairs[this_trial_staircase_id])
                    #print('This ssd is: ' + str(this_trial_ssd))
                    this_staircase_start_val = self.stairs[this_trial_staircase_id].extraInfo['thisStart']
                else:
                    this_trial_staircase_id = -1
                    this_trial_ssd = -1
                    this_staircase_start_val = -1

                trial.parameters['current_ssd'] = this_trial_ssd
                trial.parameters['staircase_id'] = this_trial_staircase_id
                trial.parameters['staircase_start_val'] = this_staircase_start_val

                print('phase durations: ' + str(trial.phase_durations))
                print(trial.parameters)

                trial.run()

                # Update staircase if this was a stop trial
                #print(self.global_log)
                if trial.parameters['stopsig_trial'] == 1.0:
                    #idx = self.global_log.shape[0]
                    #num_trial = self.global_log.loc[idx, 'trial_nr']
                    num_trial = trial.parameters['trial_nr']

                    if 'choice_key' in self.global_log:

                        if self.global_log.loc[self.global_log.trial_nr == num_trial, 'choice_key'].isna().values.all(): 
                            # Successful stop: Increase SSD
                            self.stairs[trial.parameters['staircase_id']].addData(0)
                        else:
                            # Failed stop: Decrease SSD
                            self.stairs[trial.parameters['staircase_id']].addData(1)

                    else: 
                        self.global_log['choice_key'] = np.nan
                
            self.save_data(block_nr=block_nr)
            
#             if self.subject_initials.startswith('p'): # if practice task
#                 # give feedback on task performance
#                 prac_dat = self.process_data(self.global_log)

        instructions_operator = OperatorScreen(trial_nr,ID=-1, parameters={}, phase_durations=[10000], session=self, win=self.win)
        instructions_operator.run()

        self.close()
        #self.quit()

if __name__ == '__main__':

    import datetime
    scanner = False
    subject_initials = 1
    start_block=1
    tr = 3
    gend = 'f'
    age = 1
    simulate ='y'
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%m%S")
    output_str = f'{subject_initials}_{tr}_{timestamp}_task-SST'
    output_dir = './dataSST'
    this_dir = os.getcwd()

    if simulate == 'y':
        #settings_file = '/Users/scotti/surfdrive/experiment_code/py3_SST_MSIT/IMCN-SST-MSIT/simulate_settings.yml'
        settings_file = os.path.join(this_dir, 'simulate_settings.yml')
    else:
        #settings_file = '/Users/scotti/surfdrive/experiment_code/py3_SST_MSIT/IMCN-SST-MSIT/exp_settings.yml'
        settings_file = os.path.join(this_dir, 'exp_settings.yml')

    
    # Set-up session
    sess = StopSignalSession(output_str=output_str,
                        output_dir=output_dir,
                        settings_file=settings_file,
                        start_block=start_block,
                        subject_initials=subject_initials,
                        tr=tr,
                        gend=gend,
                        age=age)

    # run
    sess.run()

