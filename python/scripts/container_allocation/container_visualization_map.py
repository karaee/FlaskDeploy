#region header
from flask import Flask, render_template
from flask_socketio import SocketIO
import webbrowser, pickle, threading,  sys

import json5
from dp import dynaplex
import sys
from enum import Enum
import numpy as np

colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#1f77b4', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896',
    '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d',
    '#9edae5' 
]

# mdp_id = "container_allocation"
# policy_name = "ppo_policy"
# seed = 324324

if len(sys.argv) != 4 and len(sys.argv) != 5:
    print(" Usage: python container_visualization_map.py <mdp_id> <policy_name> <seed> [<port_number>]")
    print(f"{len(sys.argv)}")
    sys.exit(1)
mdp_id = sys.argv[1]
policy_name = sys.argv[2]
seed = sys.argv[3]
if  len(sys.argv) == 5:
    port = sys.argv[4]
else:
    port = 5000
folder_name = mdp_id
mdp_version_number = 2
path_to_json = dynaplex.filepath("mdp_config_examples", folder_name, f"mdp_config_{mdp_version_number}" + "no_DD_no_types" + ".json")
try:
    with open(path_to_json, "r") as input_file:
        configs = json5.load(input_file)    # configs can be initialized manually with something like
except FileNotFoundError:
    raise FileNotFoundError(f"File {path_to_json} not found. Please make sure the file exists and try again.")
except:
    raise Exception("Something went wrong when loading the json file. Have you checked the json file does not contain any comment?")

mdp = dynaplex.get_mdp(**configs)



path = dynaplex.filepath(mdp.identifier(), "rollouts",  policy_name + str(seed) + ".pkl")
with open(path, 'rb') as f:
    frames = pickle.load(f)
#endregion

#region Flask
# Flask setup
app = Flask(
    __name__,
    template_folder= 'container_renderer_map_helper_files',
    static_folder='container_renderer_map_helper_files'
)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('template.html', maxFrame = len(frames)-1)

@socketio.on('request_frame')
def send_frame(data):
    index = data["index"] % len(frames)
    frame = frames[index]
    socketio.emit('update_view',
                  {"frame": frame,
                   "index": index,
                   "configs": configs,
                   "total_frames": len(frames)
                   })

def open_browser():
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:" + str(port))).start()


if __name__ == '__main__':
    open_browser()
    socketio.run(app, debug=True, port = port)
        
sys.stdout.flush()
#endregion
