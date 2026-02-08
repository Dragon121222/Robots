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
    The software is meant to run locally without any network calls. 

Design Decisions: 
    I tried making real IPC work but there are performance costs in python to having true IPC and so I am faking it. The main.py file is basically the startup script which runs each of the simple programs and coordinates them working together. 
