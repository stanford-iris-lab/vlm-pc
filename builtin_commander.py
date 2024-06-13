import lib.robot_interface as sdk
import time

HIGHLEVEL = 0xee
LOWLEVEL  = 0xff


import threading
import time


# Not actually using this class now cuz not multithreading not needed given current specs
class PersistantCommandThread(threading.Thread):
    def __init__(self, single_command_func=None):
        super(PersistantCommandThread, self).__init__()
        self._stop_event = threading.Event()

        self.single_command_func = single_command_func

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            self.single_command_func()
            time.sleep(0.02)


#TODO: Make superclasses of this class if we want to have fancier commands than "do this predefined thing for x time"
#Such a class should probably override the execute_hl_command() method (and maybe __init__ as well if needed)
class BuiltInCommandHandler:

    def __init__(self, config):

        if isinstance(config, str):
            #load from from file
            pass

        self.config = config

        self.persistant_command_thread = None

        self.udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)

        self.cmd = sdk.HighCmd()
        self.state = sdk.HighState()
        self.udp.InitCmdData(self.cmd)

        self._execute_single_command() #execute default command to set to idle
        self.last_body_height = 0


    def _set_cmd_to_default(self):
            self.cmd.mode = 0      # 0:idle, default stand      1:forced stand     2:walk continuously
            self.cmd.gaitType = 0
            self.cmd.speedLevel = 0
            self.cmd.footRaiseHeight = 0
            self.cmd.bodyHeight = 0
            self.cmd.euler = [0, 0, 0]
            self.cmd.velocity = [0, 0]
            self.cmd.yawSpeed = 0.0
            self.cmd.reserve = 0

    def _execute_single_command(self, mode=0, 
                                velocity=[0.0, 0.0],
                                gaitType=1,
                                yawSpeed=0.0,
                                reserve=0,
                                speedLevel=0,
                                footRaiseHeight=0,
                                bodyHeight=0,
                                euler=[0,0.0, 0.0]):
        self.udp.Recv()
        self.udp.GetRecv(self.state)

        self.cmd.mode = mode      # 0:idle, default stand      1:forced stand     2:walk continuously
        self.cmd.gaitType = gaitType
        self.cmd.speedLevel = speedLevel
        self.cmd.footRaiseHeight = footRaiseHeight
        self.cmd.bodyHeight = bodyHeight
        self.cmd.euler = euler
        self.cmd.velocity = velocity
        self.cmd.yawSpeed = yawSpeed
        self.cmd.reserve = reserve

        self.udp.SetSend(self.cmd)
        self.udp.Send()

    def execute_hl_command(self, hl_command, turn_back=True):

        if self.persistant_command_thread is not None:
            self.persistant_command_thread.stop()
            self.persistant_command_thread.join()
            self.persistant_command_thread = None

        action = hl_command[0].lower()

        hl_command = (hl_command[0] + " " + hl_command[1]).lower()

        if isinstance(hl_command, str):
            hl_command = self.config[hl_command]
        duration = hl_command["duration"]
        builtin_kwargs = hl_command["builtin_kwargs"].copy()

        # if action == "backward" or action == "left" or action == "right":
        #     builtin_kwargs["bodyHeight"] = self.last_body_height

        if "bodyHeight" in hl_command["builtin_kwargs"]:
            self.last_body_height = hl_command["builtin_kwargs"]["bodyHeight"]
        else:
            self.last_body_height = 0

        print(f"For {duration}s, executing:", builtin_kwargs)

        start_time = time.time()
        while time.time() < start_time + duration:
            time.sleep(0.03)
            self._execute_single_command(**builtin_kwargs)

        if turn_back and (action == 'right' or action == 'left'):
            temp_builtin_kwargs = self.config["walk medium"]["builtin_kwargs"]
            start_time = time.time()
            while time.time() < start_time + 2:
                time.sleep(0.03)
                self._execute_single_command(**temp_builtin_kwargs)

            temp_builtin_kwargs = builtin_kwargs.copy()
            temp_builtin_kwargs["yawSpeed"] = temp_builtin_kwargs["yawSpeed"] * -1
            start_time = time.time()
            while time.time() < start_time + duration:
                time.sleep(0.03)
                self._execute_single_command(**temp_builtin_kwargs)

        print("Command Finished", self.last_body_height)
        if self.last_body_height != 0.0:
            self._execute_single_command(bodyHeight=self.last_body_height, mode=2)
            self.persistant_command_thread = PersistantCommandThread(lambda: self._execute_single_command(bodyHeight=self.last_body_height, mode=2))
            self._execute_single_command(bodyHeight=self.last_body_height, mode=2)
            self.persistant_command_thread.start()
            

if __name__ == '__main__':

    command_config = {"walk":{
                        "duration": 2,
                        "builtin_kwargs":
                            {
                                "mode": 2,
                                "gaitType": 1,
                                "velocity": [0.2, 0],
                                "yawSpeed": 0
                            }
                        },
                      "backwards": {
                        "duration": 2,
                        "builtin_kwargs":
                            {
                                "mode": 2,
                                "gaitType": 1,
                                "velocity": [-0.2, 0],
                                "yawSpeed": 0
                            }
                        },
                      }
    
    handler = BuiltInCommandHandler(command_config)
    time.sleep(1)
    handler.execute_hl_command("walk")
    time.sleep(1)
    handler.execute_hl_command("backwards")
