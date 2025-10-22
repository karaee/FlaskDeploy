import json5
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
from dp import dynaplex
import sys
from enum import Enum

colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#1f77b4', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896',
    '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d',
    '#9edae5' 
]
ContainerStatus = Enum('ContainerStatus', [('Idle', 0), ('ToOrigin', 1), ('ToDestination', 2)])
class PlayBar(object):
    def __init__(self, animationIn):
        self.animation = animationIn
        self.isRunning = True
        self.button = Button(plt.axes([0.5 - 0.05, 0+0.01, 0.05, 0.05]), 'I>')
        self.button.on_clicked(self.Pause)
    def Pause(self, event):
        self.animation.event_source.stop() 
        self.button.label.set_text('II') 
        self.button.on_clicked(self.Play)
    def Play(self, event):
        self.animation.event_source.start() 
        self.button.label.set_text('I>') 
        self.button.on_clicked(self.Pause)

def visualize_dynamic_world(iter, trace, configs, ax):
    wSize = configs["worldDimensions"]
    nOrder = trace[iter]["period_count"]
    dynamic_state = trace[iter]["state"]
    if 'action' in trace[iter]:
        action = trace[iter]['action']
    else: action = -1

    # Get state variables
    time = dynamic_state["current_time"]
    cat = dynamic_state["cat"]
    if 'arrivingOrder' in dynamic_state:
        order = dynamic_state["arrivingOrder"]
    else: order = 0 
    containers = dynamic_state["containers"]
    SEQ = dynamic_state["scheduled_event_queue"]
    
    ax.clear()  # Clear previous drawings to update with new state
    ax.set_xlim(0, wSize[0])
    ax.set_ylim(0, wSize[1])

     # Constants for layout
    box_height = 0.6
    box_width = 2.0
    start_y = 5
    padding_x = 0.05 * wSize[0]
    padding_y = 0.03 * wSize[1]

    heightTruck = 1.5


    for c in containers:
        coords = containers[c]["targetLocation"]["coords"]
        if containers[c]["status"] != ContainerStatus.Idle.value:
            O = containers[c]["loadLocation"]["coords"]
            D = containers[c]["unloadLocation"]["coords"]
            alpha = 0.2
            ax.text(O[0], O[1], 'O', color=colors[int(c)], ha = 'center', va = 'center')
            ax.text(D[0], D[1], 'D', color=colors[int(c)], ha = 'center', va = 'center')
            ax.plot( [O[0], D[0]], [O[1], D[1]], color= colors[int(c)], linewidth=0.5, linestyle='--')
            if containers[c]["status"] == ContainerStatus.ToDestination.value:
                coords = O
            else:
                ax.plot( [O[0], coords[0]], [O[1], coords[1]], color= colors[int(c)], linewidth=0.5, linestyle='--')
        else:
            alpha = 1
        anchor = [coords[0]-heightTruck/2, coords[1]-heightTruck/2]
        square = patches.Rectangle(anchor, heightTruck, heightTruck, color = 'black', alpha = alpha)
        ax.add_patch(square)
        ax.text( coords[0],coords[1] - padding_y ,containers[c]["index"], color='black', ha = 'center', va = 'center')

    # Write time, order count and action

    message = ""
    color = "black"

    if cat["await"] == "action":
        message = f"\nTaking action!"
    else:
        if "index" in cat:
            if cat["index"] == 11:
                action = SEQ[0]["action_index"]
                message = f"\nContainer {action} is assigned."
                color = 'green'  
            elif cat["index"] == 12:
                color = 'red'
                message = f"\nOrder is lost!"
            elif cat["index"] == 13:
                action = SEQ[0]["action_index"]
                message = f"\nContainer {action} at origin."
            elif cat["index"] == 14:
                action = SEQ[0]["action_index"]
                message = f"\nContainer {action} at destination."
            else:
                raise Exception("Unexpected awaiting event index!")
        else:
            message = f"\nWaiting for order arrival"

    if order:
        origin = order["o"]
        destination = order["d"]
        orderType = order["typeKey"]
        ax.text(origin['coords'][0], origin['coords'][1], f"O{orderType}", color=color, ha = 'center', va = 'center')
        ax.text(destination['coords'][0] , destination['coords'][1], f"D{orderType}", color=color, ha = 'center', va = 'center')
    
    ax.set_title(f"Current time: {time}\n Order count: {nOrder}{message}")
    # ax.axis('off')  # Hide the axes

folder_name = "container_allocation"
mdp_version_number = 0
path_to_json = dynaplex.filepath("mdp_config_examples", folder_name, f"mdp_config_{mdp_version_number}.json")
try:
    with open(path_to_json, "r") as input_file:
        configs = json5.load(input_file)    # configs can be initialized manually with something like
except FileNotFoundError:
    raise FileNotFoundError(f"File {path_to_json} not found. Please make sure the file exists and try again.")
except:
    raise Exception("Something went wrong when loading the json file. Have you checked the json file does not contain any comment?")

mdp = dynaplex.get_mdp(**configs)
policy = mdp.get_policy("random")
demonstrator = dynaplex.get_demonstrator(max_period_count=100)
trace = demonstrator.get_trace(mdp,policy)

nContainer = len(configs['initialLocations'] )

# Setup figure and axes for the animation
fig, ax = plt.subplots(figsize=(16, 9))
# Create the animation
ani = FuncAnimation(fig, visualize_dynamic_world, frames=range(1, 500), fargs=(trace, configs, ax), repeat=False, interval = 200)
playBar = PlayBar(ani)

# with open("myvideo.html", "w") as f:
#     print(ani.to_html5_video(), file=f)

# ani.save(dynaplex.filepath("movies","animation.gif"), writer='Pillow', fps=2)
# plt.show()
