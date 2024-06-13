if __name__ == "__main__":
    import sys
    sys.path.append('../')
    from hl_controller import VLM_HL_Controller
else:
    from .hl_controller import VLM_HL_Controller
import time
import copy
from PIL import Image
import base64
import io


initial_critic_text = "You are controlling a robot dog to get through obstacles. The goal is to make forward progress in this starting direction and find a red dog chew toy on the other side of the obstacles in front of you. The actions the robot can take are Walk, Crawl, Left, Right, Backward, Climb. The robot dog should Crawl when it should go under an obstacle, Climb when it should go over the obstacle, turn Left when it should turn left to get around an obstacle, and turn Right when it should turn right to get around the obstacle. Right/Left command inplace turns, meaning that the robot will change the direction it it facing but not its position. This means that command a turn is commanded, the robot needs another command afterwards to move forwards in order to move in the new direction. The robot should go Backward if the camera is obscured and it is not clear what other action to take. If there is space to walk forward in front of the robot, the command should be Walk.\n\nFirst, I am going to show you what has already happened recently. I will show you a series of images that are what the robot dog saw in front of it at each time followed by the action the robot initiated at that time. The images in the series are in order of the time they were taken."


prompt_critic_text = "Based on the history of images and actions I have just shown you and PLAN 1, which I will describe to you in a moment, I want you to reason through the strategy I am trying to use to. Is this strategy working as intended? Why or why not? If not, what is stopping it from working?\n\nNext I will show you what the robot dog currently sees in front of it. I will describe to you two plans for how to proceed at getting through these obstacles to find the chew toy. PLAN 1 is the plan I have recently been using to control the robot while PLAN 2 is a new proposed plan. These plans also include the action to take right now in order to follow each of these plan:\n\n{INSERT PLANS}\n\n I want you to reason through which plan is better. Which is more likely to succeed, given what has already been tried and what the robot currently sees? Chose one of the plans and explain why you think that plan is better. Then tell me the next action to take and the magnitude that action should have in order to begin executing the chosen plan. The third to last word of your response should be the plan you chose in the format 1/2. The second to last word of your response should be the next action take take, in other words the next action in the plan you chose, in the format Walk/Crawl/Left/Right/Backward/Climb. The last word of you response should be the magnitude of that action in the format Small/Medium/Large.  Once again, the last three words of your response must be the plan your chose and the action from the new plan, in the format 1/2 Walk/Crawl/Left/Right/Backward/Climb Small/Medium/Large."


proposer_init_prompt = "You are controlling a robot dog to get through obstacles. The goal is to find a red dog chew toy on the other side of the obstacles in front of you. If you try going under or over an obstacle and are unable to make reliable forward progress, try going around the obstacle. After each action you command the robot to take, you will be given a new image taken from the head of the robot dog. Each time you receive an image, you must command one of the following six actions: Walk, Crawl, Left, Right, Backward, Climb. You should command Crawl when it should go under an obstacle, command Climb when it should go over the obstacle; if you think it is possible to go under the obstacle, try to Crawl at least once and if you think it is possible to go over an obstacle, try to Climb at least once. Command Left when it should go left to get around an obstacle, and Right when it should go right to get around the obstacle. Right/Left command inplace turns, meaning that the robot will change the direction it it facing but not its position. This means that if you command a turn, you need to move forwards in order to move in the new direction. You should command the robot Backward if the camera is obscured and it is not clear what other action to take. If there is space to walk forward in front of you, you should command Walk. You should reason through the history of what actions you have selected and the scene. If an action seems to be working, keep performing that action. If an action does not seem to be working, try a different action. If you ever command backwards, do not try to do the same action you did before you commanded backwards again immediately (you may do so later once you are in a different scenario). In your response, describe a plan for how to get around the obstacles and find the chew toy and reasons that plan might fail. The second to last word of your output should be the action to take. The last word of your response should be a magnitude (Small, Medium, Large) that specifies how much of that action to take. In general, err on the side of taking lower magnitude actions unless you are confident you can continue an action for several seconds without running into obstacles or loosing your bearings. Once again, the last two words of your response must be in the format Walk/Crawl/Left/Right/Backward/Climb Small/Medium/Large."

prefix_proposer_continuing_prompt = "I chose to adopt PLAN {plan_choice} you described in your last response. "
proposer_continuing_prompt = "Based on this plan, I executed the action {last_action} and the robot has moved. Here is what the robot currently sees. Remember your ultimate objective of finding the red chew toy. I want you to summarize your this previous plan (now call this plan PLAN 1), then reason about the state of the robot including its current position and orientation and if it has made progress with your previous plan. Based on this previous plan, I want you to output what action you would now take next. Make sure this action is described in the format Walk/Crawl/Left/Right/Backward/Climb Small/Medium/Large. Then, I want you to reassess the situation and come up with a completely new plan (call this PLAN 2). Make sure to describe why the plan might fail. Based on this new plan, I want you to output what action you would take next. Make sure this action is described in the format Walk/Crawl/Left/Right/Backward/Climb Small/Medium/Large. This action should also be the last two words of your response. Once again, the last two words of your response must be the action from the new plan, in the format Walk/Crawl/Left/Right/Backward/Climb Small/Medium/Large."

def encode_image(image, output_size=(400, 300), quality=85):
    # Open the image and resize it

    with Image.fromarray(image) as img:
        img = img.resize(output_size, Image.Resampling.LANCZOS)

        # Save the resized image to a bytes buffer
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', quality=quality)

        # Encode to base64
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

def append_to_message_hist_as_user(message_hist, text=None, image=None):
    if text is not None:
        new_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    },
                ]
            }
        ]
        message_hist.extend(new_message)

    if image is not None:

        image_base64 = encode_image(image)

        new_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    }
                ]
            }
        ]
        message_hist.extend(new_message)


class ProposerCritic_VLM_HL_Controller(VLM_HL_Controller):

    def __init__(self, latest_image_func, vlm_query_func,
                  hl_command_handle_func,
                 logdir="log", interval=3, turn=False):
        super().__init__(latest_image_func, vlm_query_func, hl_command_handle_func,
                          "", logdir, interval, turn)
        del self.opening_query_text

    def query(self):
        count = 0

        proposer_message_hist = []

        critic_prior_message_hist = []

        while self.running:
            start_time = time.time() - self.reference_time

            while time.time() - self.last_query < self.interval:
                time.sleep(0.05)

            image = self.latest_image_func()

            if count == 0:
                image = self.latest_image_func()
                response = self.vlm_query_func(image, proposer_init_prompt, proposer_message_hist)
                result = self.get_last_n_words(response, 2)
                record_message_hist = {"proposer": copy.deepcopy(proposer_message_hist)}

                record_response = response

                append_to_message_hist_as_user(critic_prior_message_hist, text=initial_critic_text)
                
            else:
                image = self.latest_image_func()
                proposer_prompt = proposer_continuing_prompt.replace("{last_action}", self.last_action)
                if count > 1:
                    proposer_prompt = prefix_proposer_continuing_prompt.replace("{plan_choice}", self.last_plan_choice) + proposer_prompt
                proposer_response = self.vlm_query_func(image, proposer_prompt, proposer_message_hist)

                critic_prompt = prompt_critic_text.replace("{INSERT PLANS}", proposer_response)

                critic_history_for_this_timestep = copy.deepcopy(critic_prior_message_hist)
                critic_response = self.vlm_query_func(image, critic_prompt, critic_history_for_this_timestep)

                result = self.get_last_n_words(critic_response, 3)
                self.last_plan_choice = result[0]
                result = result[1:]

                record_response = critic_response

                record_message_hist = {"proposer": copy.deepcopy(proposer_message_hist),
                                       "critic": critic_history_for_this_timestep}


            append_to_message_hist_as_user(critic_prior_message_hist, image=image)
            append_to_message_hist_as_user(critic_prior_message_hist, text=" ".join(result))

            self.last_action = '"' + " ".join(result) + '"'

            return_time = time.time() - self.reference_time

            self.query_queue.put((image, "", record_response, result, start_time, return_time, record_message_hist))

            self.hl_command_handle_func(result, self.turn)
            
            self.last_query = time.time()

            count += 1

if __name__ == "__main__":
    import numpy as np

    sim_controller = ProposerCritic_VLM_HL_Controller(latest_image_func=lambda: np.empty((100, 100), dtype=np.int32),
                                                      vlm_query_func=lambda x, y, z: "Crawl Small",
                                                      hl_command_handle_func=lambda x, y: None)
    
    sim_controller.set_reference_time(time.time())
    
    sim_controller.query()