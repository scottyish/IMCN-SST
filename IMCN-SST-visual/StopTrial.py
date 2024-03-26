from exptools2.core.trial import Trial
#from exptools2.core import Session
from psychopy import event, visual
from StopStimulus import FeedbackCorrect, FeedbackWrong, FeedbackStop
import pandas as pd
import numpy as np
from psychopy.sound.backend_sounddevice import SoundDeviceSound

#class StopSignalTrial(MRITrial):
class StopSignalTrial(Trial):

    def __init__(self, trial_nr, parameters, phase_durations, session=None, phase_names=None):
        super(StopSignalTrial, self).__init__(trial_nr=trial_nr,
                                              parameters=parameters,
                                              phase_durations=phase_durations,
                                              phase_names=phase_names,
                                              session=session)

        # Define whether trial should run as practice session
        self.practicing = None
        if self.session.subject_initials.startswith('p'):
            self.practicing = True
        else:
            self.practicing = False

        # setup other important variables
        self.trial_nr = trial_nr
        self.trs_recorded = 0
        self.has_bleeped = False
        self.response_measured = False  # Has the pp responded yet?
        self.response = None
        self.rt = -1
        self.bleep_time = -1
        self.parameters = parameters
        self.measure_first_phase = False
        self.phase0_start = None
        self.null_trial = parameters['null_trial']

        # setup number of trs from input design to line up MRI with expriment code
        if 'n_trs' in parameters.keys():
            self.stop_on_tr = parameters['n_trs']
        else:
            self.stop_on_tr = None

        # setup feedback objects
        self.correct_resp = FeedbackCorrect(self.session.win)
        self.wrong_resp = FeedbackWrong(self.session.win)
        self.stop_resp = FeedbackStop(self.session.win)
        self.fb_object = None

        # setup responses
        self.response={}
        self.response['choice_key'] = None
        self.response['rt'] = None

        # Should the arrow display left or right? 
        if parameters['direction'] in ['NaN','nan','nan.'] or pd.isna(parameters['direction']):
            self.stim = None
        else:    
            if bool(parameters['direction']):
                self.stim = self.session.left_stim
            else:
                self.stim = self.session.right_stim

        # is it a stop trial? 
        if parameters['stopsig_trial'] in ['NaN','nan','nan.'] or pd.isna(parameters['stopsig_trial']):
            self.stopsig_trial = False
        else:
            if bool(parameters['stopsig_trial']):
                self.stopsig_trial = True
            else:
                self.stopsig_trial = False

    # Function to find out what events occur (button press, MRI trigger etc)
    def get_events(self):
        """ evs, times can but used to let a child object pass on the evs and times """

        evs = event.getKeys(timeStamped=self.session.clock)        

        for ev, time in evs:
            if len(ev) > 0:

                if ev == 'q': # button to quit session
                    print('q button pressed (session will quit)')
                    self.session.close()
                    self.session.quit()
                elif ev == 'equal' or ev == '+': 
                    self.stop_trial()

                idx = self.session.global_log.shape[0]

                # TR pulse
                if ev == self.session.mri_trigger:
                    event_type = 'pulse'
                    self.trs_recorded += 1

                    if self.stop_on_tr is not None:
                        # Trial ends whenever trs_recorded >= preset number of trs
                        if self.trs_recorded >= self.stop_on_tr:
                            self.stop_trial()

                elif ev in self.session.response_button_signs:
                    event_type = 'response'
                    if self.phase == 1:
                        if not self.response_measured:
                            self.response_measured = True
                            self.process_response(ev, time, idx)

                            # Not in the MR scanner? End phase upon keypress
                            # if not self.session.in_scanner and self.phase == 3:
                            #     self.stop_phase()
                else:
                    event_type = 'non_response_keypress'
                    #self.session.global_log.loc[idx, 'choice_key'] = np.nan

                # global response handling
                self.session.global_log.loc[idx, 'trial_nr'] = self.trial_nr
                self.session.global_log.loc[idx, 'block_nr'] = self.parameters['block_nr']
                self.session.global_log.loc[idx, 'onset'] = time
                self.session.global_log.loc[idx, 'event_type'] = event_type
                self.session.global_log.loc[idx, 'phase'] = self.phase
                self.session.global_log.loc[idx, 'response'] = ev
                self.session.global_log.loc[idx, 'SSD'] = self.parameters['current_ssd']

                for param, val in self.parameters.items():
                    self.session.global_log.loc[idx, param] = val

                if self.eyetracker_on:  # send msg to eyetracker
                    msg = f'start_type-{event_type}_trial-{self.trial_nr}_phase-{self.phase}_key-{ev}_time-{time}'
                    self.session.tracker.sendMessage(msg)

                if ev != self.session.mri_trigger:
                    self.last_resp = ev
                    self.last_resp_onset = time
                    self.session.global_log.loc[idx, 'choice_key'] = self.response['choice_key']

    # Process the responses picked up by get_events
    def process_response(self, ev, time, idx):
        """ Processes a response:
        - checks if the keypress is correct/incorrect;
        - checks if the keypress was in time;
        - Prepares feedback accordingly """

        self.response['choice_key'] = ev

        # to calculate response time, look up stimulus onset time
        log = self.session.global_log

        stim_onset_time = log.loc[(log.trial_nr == self.trial_nr) & (log.event_type == 'stimulus'), 'onset'].values[0]

        self.response['rt'] = time - stim_onset_time

        # if they respond with an acceptable button
        if ev in self.session.response_button_signs:
            
            print('button pressed')

            # Show correct/incorrect feedback on practice trials
            # only show feedback on practice task
            if self.practicing == True and self.stim is not None: # if trial is practice and it is not a null trial
                if ((ev == str(self.session.response_button_signs[0]) and bool(self.parameters['direction']) and not self.stopsig_trial)
                        or (ev == str(self.session.response_button_signs[1]) and not bool(self.parameters['direction']) and not self.stopsig_trial)):
                    print('correct choice')
                    self.fb_object = self.correct_resp
                elif (ev != None and self.stopsig_trial):
                    self.fb_object = self.stop_resp
                    print('did not stop')
                else:
                    self.fb_object = self.wrong_resp
                    print('incorrect choice')

        else: # if they did not press a button
            print('no button pressed')

        self.session.global_log.loc[idx, 'rt'] = self.response['rt']
        self.session.global_log.loc[idx, 'choice_key'] = self.response['choice_key']   
        
    # Function to draw the phases of the experiment
    def draw(self):

        """
        Phases:
        0 = fixation circle (jittered timing)
        1 = stimulus (left or right arrow) + stop signal 
        2 = feedback (for practice trials only)
        3 = blank screen
        """

        if self.phase in [0,1,2]: # show fixation on all phases
            if not self.null_trial:
                self.session.fixation_circle.draw()
            if self.measure_first_phase == False:
                self.phase0_start = self.session.clock.getTime()
                self.measure_first_phase = True

        if self.phase == 1: # display stimulus arrow on phase 1
            if self.stim is not None:
                self.stim.draw()

            if self.stopsig_trial and not self.has_bleeped and self.phase0_start is not None:
                if ((self.session.clock.getTime() > self.phase0_start + self.parameters['jitter'] + self.parameters['current_ssd']) and
                (self.session.clock.getTime() < self.phase0_start + self.parameters['jitter'] + self.parameters['current_ssd'] + 0.3)): # +0.3 because we show stop signal for 300ms
                    self.session.stop_circle.draw()
                    #self.has_bleeped = True

        if self.phase == 2 and self.practicing == True: # Only show feedback on practice task
            if self.fb_object is not None:
                self.fb_object.draw()
        
##################################        
####### Instruction texts ########
##################################

# MAKE ONE FUNCTION TO DO ALL INSTRUCTION TEXTS
class AllInstructions(Trial):

    def __init__(self, trial_nr,ID, parameters, phase_durations, session=None, win=None, instruct_num=None):
        super(AllInstructions, self).__init__(trial_nr=trial_nr,
                                              phase_durations=phase_durations,
                                              session=session
                                              )
        self.win = win
        self.ID = ID
        self.parameters = parameters
        self.instruct_num = instruct_num

        nblocks = len(np.unique(self.session.design.block))

        # DEFINE INSTRUCTIONS
        if self.instruct_num == 1: # waiting for scanner text

            task_instructions = ["Waiting for scanner"]
            self.wait_screen = 'y' # if waiting for scanner screen don't allow 'space' to skip the phase. Wait for trigger.

        elif self.instruct_num == 2: # main instructions

            task_instructions = ["INSTRUCTIONS","","Each trial, you will be presented with a left or right arrow.","Press the button corresponding to the direction of the arrow that you see.",
                                "The values corresponding to the buttons are:","left index finger = left arrow, right index finger = right arrow","","The response buttons are:","red = left and blue = right","",
                                "The arrow will be surrounded by a white circle for most of the time.", "On a subset of trials, you will see a red circle.",
                                "If you see this red circle you should not respond at all to the", "arrow on the screen, and simply wait for the next trial.","",
                                "Press < space > to continue"]
            self.wait_screen = 'n'

        elif self.instruct_num == 3: # practice task overview

            task_instructions = ["PRACTICE TASK","","You will now start a practice session of the stop-signal task.",
                                "There will be " + str(len(self.session.design.block)//nblocks) + " practice trials.","","Press < space > to continue to the instructions"]
            self.wait_screen = 'n'

        elif self.instruct_num == 4: # scanner task overview

            if nblocks > 1:
                def_block = 'blocks'
            else:
                def_block = 'block'

            task_instructions = ["EXPERIMENTAL TASK","","You will now start the experimental", "session of the stop-signal task.",
                                "There will be " + str(nblocks) + " " + def_block + " of " + str(len(self.session.design.block)//nblocks) + " trials.", "",
                                "Press < space > to start the task"]
            self.wait_screen = 'n'

        elif self.instruct_num == 5: # task is about to start text

            task_instructions = ["The task is about to start,","please have your fingers ready", "on the response buttons"]
            self.wait_screen = 'n'
            
        elif self.instruct_num == 6: # continue the instructions
        
            task_instructions = ["Important:", 
                                "Do not wait for this red circle (the stop-signal), you", "should respond as quickly and as accurately as possible on all trials.","","Remember:", "Stopping and going are equally important.", "",
                                "Press < space > to start the practice task"]
            self.wait_screen = 'n'

        self.instruction_text = self.gen_instructions(task_instructions, deg_per_line=self.session.line_space, bottom_pos=len(task_instructions))

    def get_events(self):

        for ev, time in event.getKeys(timeStamped=self.session.clock):
            if len(ev) > 0:

                idxs = self.session.global_log.shape[0]

                if ev == 'q': # quit
                    print('q button pressed during instructions (session will quit)')
                    self.session.close()
                    self.session.quit()
                elif (ev == 'equal' or ev == '+') and self.wait_screen=='n': # skip trial
                    self.stop_trial()

                # move to next phase
                if self.wait_screen == 'n':
                    if ev == 'space':
                        self.last_key = ev
                        self.stop_phase()
                
                # move to next phase if on waiting screen
                elif self.wait_screen == 'y':
                    if ev == self.session.mri_trigger:
                        self.session.ev_to_start += 1
                        self.last_key = ev
                        if self.session.ev_to_start == 4:
                            self.stop_phase()

                # TR pulse
                if ev == self.session.mri_trigger:
                    event_type = 'pulse'
                elif ev in self.session.response_button_signs:
                    event_type = 'response'
                else:
                    event_type = 'non_response_keypress'

                # global response handling
                self.session.global_log.loc[idxs, 'trial_nr'] = self.trial_nr
                self.session.global_log.loc[idxs, 'onset'] = time
                self.session.global_log.loc[idxs, 'event_type'] = event_type
                self.session.global_log.loc[idxs, 'response'] = ev

    def draw(self):

        if self.phase == 0:   # waiting for scanner-time
            #self.instruction_text.draw()
            for ins in self.instruction_text:
                ins.draw()
        
    def gen_instructions(self, input_text, deg_per_line=1.5, bottom_pos=5, wrapWidth=100):

        text_objects = []

#         if deg_per_line < 1:
#             if bottom_pos == 7:
#                 bottom_pos -= bottom_pos*0.7
#             elif bottom_pos == 3:
#                 bottom_pos -= bottom_pos*0.65
#             elif bottom_pos == 1:
#                 bottom_pos -= bottom_pos*0.5
#             else:
#                 bottom_pos = bottom_pos

        for i, text in enumerate(input_text):
            text_objects.append(visual.TextStim(win=self.win, text=text, pos=(0,bottom_pos*0.5-i*deg_per_line), alignVert='bottom',
                                wrapWidth=wrapWidth,height=self.session.settings['stimulus']['instructSize']))

        return text_objects


# MAKE ONE CLASS JUST TO DO WAITING FOR OPERATOR SCREEN BECAUSE IM LAZY
class OperatorScreen(Trial):

    def __init__(self, trial_nr,ID, parameters, phase_durations, session=None, win=None):
        super(OperatorScreen, self).__init__(trial_nr=trial_nr,
                                              phase_durations=phase_durations,
                                              session=session
                                              )
        self.win = win
        self.ID = ID
        self.parameters = parameters

    def get_events(self):

        for ev, time in event.getKeys(timeStamped=self.session.clock):
            if len(ev) > 0:

                idxs = self.session.global_log.shape[0]

                if ev == 'q': # quit
                    print('q button pressed during operator screen (session will quit)')
                    self.session.close()
                    self.session.quit()

                # elif (ev == 'equal' or ev == '+') and self.wait_screen=='n': # skip trial
                #     self.stop_trial()

                # move to next phase if operator button pressed
                if ev == self.session.operator_button: # end phase
                        self.last_key = ev
                        self.stop_phase()

                # TR pulse
                if ev == self.session.mri_trigger:
                    event_type = 'pulse'
                elif ev in self.session.response_button_signs:
                    event_type = 'response'
                else:
                    event_type = 'non_response_keypress'

                # global response handling
                self.session.global_log.loc[idxs, 'trial_nr'] = self.trial_nr
                self.session.global_log.loc[idxs, 'onset'] = time
                self.session.global_log.loc[idxs, 'event_type'] = event_type
                self.session.global_log.loc[idxs, 'response'] = ev

    def draw(self):

        if self.phase == 0:   # waiting for scanner-time
            #self.instruction_text.draw()
            visual.TextStim(win=self.win, text='Waiting for operator', alignVert='bottom', pos=(0,0), 
                                wrapWidth=100,height=self.session.settings['stimulus']['instructSize']).draw()
            #for ins in self.instruction_text:
            #    ins.draw()