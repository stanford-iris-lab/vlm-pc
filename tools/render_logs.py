from adjusted_display_message_log import *
from log_movie_maker import *
from calculate_time import *
import os
import json


import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--logdir", required=True)

args = parser.parse_args()

for fname in os.listdir(args.logdir + "/vlm"):
    if not("log" in fname) and ".json" in fname:
        print(fname)
        with open(args.logdir + "/vlm/" + fname, 'r') as f:
            messages = json.load(f)
        save_chat_to_pdf(messages, args.logdir + "/vlm/" + fname.replace(".json", ".pdf"))

compute_stats(args.logdir, True)

create_movie(args.logdir)
