# VLM-Predictive Control (VLM-PC)

This code implements the following paper:

TODO

## Abstract
Legged robots are physically capable of navigating a diverse variety of environments and overcoming a wide range of obstructions. For example, in a search and rescue mission, a legged robot could climb over debris, crawl through gaps, and navigate out of dead ends. However, the robot's controller needs to respond intelligently to such varied obstacles, and this requires handling unexpected and unusual scenarios successfully. This presents an open challenge to current learning methods, which often struggle with generalization to the long tail of unexpected situations without heavy human supervision. To address this issue, we investigate how to leverage the broad knowledge about the structure of the world and commonsense reasoning capabilities of vision-language models (VLMs) to aid legged robots in handling difficult, ambiguous situations. We propose a system, VLM-Predictive Control (VLM-PC), combining two key components that we find to be crucial for eliciting on-the-fly, adaptive behavior selection with VLMs: (1) in-context adaptation over previous robot interactions and (2) planning multiple skills into the future and replanning. We evaluate VLM-PC on several challenging real-world obstacle courses, involving dead ends and climbing and crawling, on a Go1 quadruped robot. Our experiments show that by reasoning over the history of interactions and future plans, VLMs enable the robot to autonomously perceive, navigate, and act in a wide range of complex scenarios that would otherwise require environment-specific engineering or human guidance.

## Hardware Setup

1. Print the mount listed as `frontmount v9.stl` using a 3D printer of your choice (PLA should be fine). Mount your camera into the protected space on the front of the mount, and then mount the assembly through the neck holes of the robot, such that the camera mount hangs over the robot's head.

4. Chose one of your Go1 Edu's Nanos. Use a USB hub to connect this Nano to a USB wifi adapter and the realsense camera on the front of the robot.



## Installation

1. Clone this repo to your chosen Nano on your Go1 Edu (Here we will assume you are using Nano3 at 192.168.123.15)

```
git clone https://github.com/stanford-iris-lab/vlm-pc.git
cd vlm-pc
```

2. Create a new mamba environment running Python 3.8. Using the conda-forge channel may be helpful to resolve combatability issues with the architecture of the Nano

```
mamba create -n vlmpc python=3.8
mamba activate vlmpc
```
3. Install dependencies via `pip`
```
pip install pyrealsense2==2.55.1.6486
pip install pillow==10.3.0
pip install numpy
```

## Running and Configs

To run VLM-PC with default settings, run
```
python run_hl.py --logdir experiment_name
```
To make a custom command configuration for the Go1 Controller, make a new json file in `configs/commands` in the format of `default.json`. Then use `python run_hl.py --command_config` to use the new command profile.

To make a custom controller profile (for example, to use custom prompts or use a custom ICL dataset), make a new json file in `configs/controller` with edited prompts. Then use `python run_hl.py --control_config` to use this new config file. The config files included in `configs/controller` implement VLM-PC and all the ablations described in the paper. 

To specify a new ICL dataset, make a new folder with ICL images (see `configs/icl` as an example). Name each image with the possible commands to use in each scenario separated by `_`. Then add `"icl": directory/of/new/icl/dataset` to the controller config json file to use this dataset. Also add `<ICL>` to the location in the openning query prompt where you want to include the ICL datset. See `configs/controller/trials_history_plan_icl.json` as an example of the syntax for this.

