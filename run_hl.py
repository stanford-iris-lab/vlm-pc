from imager_collector import ImageCollector
from controllers import *
from gpt4_interface import query_gpt4v, query_gpt4v_mult
import time
from builtin_commander import BuiltInCommandHandler
import argparse
import json
import os
import copy
from datetime import datetime
import shutil


parser = argparse.ArgumentParser(description="Run VLM HL Controller.")
parser.add_argument("--logdir", required=True)
parser.add_argument("--command_config", default="configs/commands/default.json")
parser.add_argument("--control_config", default="configs/controller/trials_history_plan.json")
parser.add_argument('--duration', type=float, default=1000.)
parser.add_argument('--save_imstream', action='store_true')

args = parser.parse_args()

args.logdir = args.logdir + '/' + args.control_config.split("/")[-1][:-4] + "_" + datetime.now().strftime("%m_%d_%H_%M")
if not os.path.exists("log/" + args.logdir):
    os.makedirs("log/" + args.logdir + "/")
    os.makedirs("log/" + args.logdir + "/code_state")

os.system("cp *.py " + "log/" + args.logdir + "/code_state/")
os.system("cp */*.py " + "log/" + args.logdir + "/code_state/")
os.system("cp -r configs " + "log/" + args.logdir + "/code_state/")

args.logdir = 'log/' + args.logdir 

with open(args.control_config, 'r') as f:
    control_config = json.load(f)

with open(args.command_config, 'r') as f:
    command_config = json.load(f)

with open(args.logdir + "/args.json", 'w') as f:
    json.dump(vars(args), f, indent=4)

with open(args.logdir + "/control_config.json", 'w') as f:
    json.dump(control_config, f, indent=4)

with open(args.logdir + "/command_config.json", 'w') as f:
    json.dump(command_config, f, indent=4)


im_collector = ImageCollector(logdir=args.logdir if args.save_imstream else None)
builtin_handler = BuiltInCommandHandler(command_config)

hl_controller_class = eval(control_config["ControllerClass"])
print(hl_controller_class)

hl_controller = hl_controller_class(latest_image_func=im_collector.get_latest_image,
                                                        vlm_query_func=query_gpt4v,
                                                        hl_command_handle_func=builtin_handler.execute_hl_command,
                                                        logdir=args.logdir,
                                                        **control_config["ControllerConfig"])

reference_time = time.time()
im_collector.set_reference_time(reference_time)
hl_controller.set_reference_time(reference_time)

im_collector.start()
time.sleep(1)
hl_controller.start()

time.sleep(args.duration)

im_collector.stop()
hl_controller.stop()

builtin_handler.execute_hl_command() # return to default command state
