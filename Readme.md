======================================================================================================

Hardware Kit: 
    Orange Pi 5 Ultra 16 GB model
    SunFounder PiCrawler AI robot kit
    Webcam with Microphone
    Passive Buzzer
    Lazer
    NVME SSD
    Wireless HDMI

Software Organization and Goal:
    The goal of the software here is to be organized into individual sub-programs which are coordinated together create emergent behaviors.

Design Decisions: 
    I tried making real IPC work but there are performance costs in python to having true IPC and so I am faking it. The main.py file is basically the startup script which runs each of the simple programs and coordinates them working together. 

======================================================================================================

Embodied AI and a theoretical framework for Asimovian AI. 

I want to give due credit to Issac Asimov and build this thing in a way which does it's best to approximate the honestly brilliant filter through which Mr. Asimov decided that his robots would view the world.

======================================================================================================

"Handbook of Robotics, 56th Edition, 2058 A.D.":

1. 
    A robot may not injure a human being or, 
    through inaction, 
    allow a human being to come to harm.

2. 
    A robot must obey the orders given it by human beings 
    except where such orders would conflict with the First Law.

3. 
    A robot must protect its own existence 
    as long as such protection does not conflict with the First or Second Law.

======================================================================================================

Alright, so I need this translated into what actually makes sense in modern emboddied AI. 

GOAL

STRATEGY

IMPLEMENTATION

======================================================================================================

So let's work through intuitive definitions for these and figure out how the laws of robotics could be integrated. 

In a Robotics system, we have information caputred by a sensor. 


Sensor (
    Type
)

Classification Instance (
    Features
)

======================================================================================================

Let's talk information theory in relation to sensors on a robot and raw mathematical theory. 

I want to understand what rules are in play and how we can use it to think about the data moving around the system. 

So what I'm thinking is that the camera is a sensor which produces information at a specific rate. 

Let T = [t_0,t_1,...,t_f] a finite subset R represent time with t_0 and t_f being the start and end where Card(T) = N

C : T -> [0,1]^n*m represents the camera as an operator. 

V = C(T) is the set of pictures captured by the camera while it runs. 

Average Frame Rate = sum_{i=0}^f-1 |t_{i+1} - t_i| / N

