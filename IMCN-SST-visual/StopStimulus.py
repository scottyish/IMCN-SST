from psychopy import visual

class StopStimulus(object):

    def __init__(self, win, direction=0, arrow_size_horizontal_degrees=4):
        self.win = win
        self.direction = direction
        self.arrow_size_horizontal_degrees = arrow_size_horizontal_degrees

        if self.direction == 0:
            # Left stimulus
            vertices = [(0.2, 0.05),
                        (0.2, -0.05),
                        (0.0, -0.05),
                        (0, -0.1),
                        (-0.2, 0),
                        (0, 0.1),
                        (0, 0.05)]
        else:
            # right stimulus
            vertices = [(-0.2, 0.05),
                        (-0.2, -0.05),
                        (-.0, -0.05),
                        (0, -0.1),
                        (0.2, 0),
                        (0, 0.1),
                        (0, 0.05)]

        self.arrow = visual.ShapeStim(win=self.win, vertices=vertices, fillColor='white',
                                      size=arrow_size_horizontal_degrees, lineColor='white',
                                      units='deg',
                                      lineColorSpace='rgb', fillColorSpace='rgb')

    def draw(self):
        self.arrow.draw()


class FixationCircle(object):

    def __init__(self, win, circle_radius_degrees=4, line_width=1.5, line_color='white'):
        self.win = win
        self.circle_size_degrees = circle_radius_degrees

        self.circle_stim = visual.Circle(win=self.win,
                                         radius=circle_radius_degrees, edges=50, lineWidth=line_width,
                                         lineColor=line_color, units='deg',
                                         lineColorSpace='rgb', fillColorSpace='rgb')

    def draw(self):
        self.circle_stim.draw()

class StopCircle(object):

    def __init__(self, win, circle_radius_degrees=4, line_width=1.5, line_color='red'):
        self.win = win
        self.circle_size_degrees = circle_radius_degrees

        self.circle_stim = visual.Circle(win=self.win,
                                         radius=circle_radius_degrees, edges=50, lineWidth=line_width,
                                         lineColor=line_color, units='deg',
                                         lineColorSpace='rgb', fillColorSpace='rgb')

    def draw(self):
        self.circle_stim.draw()

class FeedbackCorrect(object):

    def __init__(self, win):
        self.win = win
        
        self.correctness = visual.TextStim(win=self.win, text='correct',color='green',
                                           pos=(0,0),font='Helvetica Neue',height=2.1)
        
    def draw(self):
        self.correctness.draw()
        
class FeedbackWrong(object):

    def __init__(self,win):
        self.win = win
        
        self.wrongness = visual.TextStim(win=self.win, text='wrong',color='red',
                                         pos=(0,0),font='Helvetica Neue',height=2.1)
    def draw(self):
        self.wrongness.draw()
        
class FeedbackStop(object):

    def __init__(self,win):
        self.win = win
        
        self.stopness = visual.TextStim(win=self.win, text='try to stop',color='red',
                                         pos=(0,0),font='Helvetica Neue',height=1.9)
    def draw(self):
        self.stopness.draw()