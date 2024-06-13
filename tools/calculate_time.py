import os
import json

def read_result_attributes(folder_path):
    res_attributes = []

    # Iterate through all files in the given folder
    for filename in os.listdir(folder_path):
        # Check if the file contains "log" in its name and has a .json extension
        if "log" in filename and filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                # Open and read the JSON file
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    # Add the "duck" attribute to the list if it exists
                    if "Result" in data:
                        res_attributes.append(" ".join(data["Result"]).lower())
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {file_path}: {e}")

    return res_attributes

def compute_stats(logdir, save_file=False):
    folder_path = logdir + "/vlm"
    actions = read_result_attributes(folder_path)
    with open(logdir + "/command_config.json", 'r') as f:
        data = json.load(f)
    sum_action_durations = sum([data[a]['duration'] for a in actions])
    num_actions = len(actions)

    minutes = int(sum_action_durations // 60)
    secs = sum_action_durations - minutes*60

    res_str = f"{num_actions} actions taken with summed action duration {minutes}:{secs}"
    if save_file:
        os.system(f"echo \"{res_str}\" > {logdir}/stats.txt")
    print(res_str)
    return res_str

# Example usage:

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--logdir")

    args = parser.parse_args()

    compute_stats(args.logdir, True)