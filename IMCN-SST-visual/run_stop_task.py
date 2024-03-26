from StopSignal import *
import glob
import datetime
import sys

#from psychopy import core

def main(initials, start_block, simulate, session_nr, session_tr, scanner, gend, age):

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_str = f'sub-{initials}_ses-{session_nr}_tr-{session_tr}_task-SST_{timestamp}'
    output_dir = './data_SST'
    this_dir = os.getcwd()

    if simulate == 'y':
        #settings_file = '/Users/scotti/surfdrive/experiment_code/py3_SST_MSIT/IMCN-SST-MSIT/simulate_settings.yml'
        settings_file = os.path.join(this_dir, 'simulate_settings.yml')
    else:
        #settings_file = '/Users/scotti/surfdrive/experiment_code/py3_SST_MSIT/IMCN-SST-MSIT/exp_settings.yml'
        settings_file = os.path.join(this_dir, 'exp_settings.yml')

    sess = StopSignalSession(output_str=output_str, output_dir=output_dir, settings_file=settings_file,
                        subject_initials=initials, tr=session_tr, start_block=start_block,
                        gend=gend, age=age, session_nr=session_nr)

    sess.run()

if __name__ == '__main__':
    main()

    # Force python to quit (so scanner emulator also stops)
    core.quit()