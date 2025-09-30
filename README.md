# Loud Noise Checker

## Overview

This program, that I made to check out real time/signal processing, listens to the amplitude of noise coming from a microphone and if it is louder than ambient it will offer the user a verbal notification, if it happens too frequently in a small period of time it can offer a different warning.

Additionally the program has a graphical interface where you can see a live graph of the audio data as well as logs of notifications it has sent.


## Functionality

Currently this program is limited to only working on a windows computer.

I could not get audio output to work at the same time as audio input with higher level modules so I used lower level Windows specific functionality.


## Goals

I have some goals for this project I would like to work towardsL
* Building a standalone windows application.
* Improving the audio output so it an work on more platforms.


## Build Instructions

* Install Build Requirements:
    * `pip install requirements-build.txt`
* Run **Nuitka** to build application:
    * `python -m nuitka --enable-plugin=tk-inter --windows-console-mode=disable --remove-output --onefile --windows-icon-from-ico=assets/icon.ico --standalone gui_version.py`
    * If you want to build multiple times to test/itterate I suggest removing `--remove-output`
    * If you want to debug the compiled application I suggest removing `--windows-console-mode=disable`

