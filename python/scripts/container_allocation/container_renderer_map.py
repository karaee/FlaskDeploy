#region header
from flask import Flask, render_template
from flask_socketio import SocketIO
import webbrowser, time, threading, os, sys
import pandas as pd

from dp import dynaplex
import sys
from enum import Enum
from CommonModules.problem_configurators import *
from CommonModules.policy_loaders import *

colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#1f77b4', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896',
    '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d',
    '#9edae5' 
]
ContainerStatus = Enum('ContainerStatus', [('Idle', 0), ('ToOrigin', 1), ('ToDestination', 2), ('ToDepot', 3)])
#endregion

#UpdateIOPath("")
configs = GetMDPConfigFile(folder_name = "container_allocation", mdp_version = "2", mdp_version_additional_setting = "")
#ConfigureProblem(configs, alpha=60, beta=50, gamma=80, C=10, lost_sale_M=1e10, lmbda = 0.004002)
# PLANNER POLICIES
# policy_config = GetPolicyConfigFile(folder_name = "container_allocation", policy_version = "pp1")
# configs["foresight_mode"] = True
# configs["foresight_horizon"] = 10
# configs["foresight_horizon"] = policy_config["lookahead_horizon"]
# CUSTOM POLICIES = "random", "DelayAlways", "GreedyPolicyWithDelayLex"
mdp = dynaplex.get_mdp(**configs)
policy = mdp.get_policy(id = "NearestDepotRandomized", p_rand = 0.0)
#policy = mdp.get_policy(id = "random")
#policy = GetPPOPolicy(mdp)
#policy = GetDCLPolicy(mdp, 2)
# policy = mdp.get_policy(**policy_config)
demonstrator = dynaplex.get_demonstrator(max_period_count= 50, rng_seed = 324324, policy_plan = True)
trace = demonstrator.get_trace(mdp, policy)
frames = trace
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
                  {"period_count": frame["period_count"],
                   "action": frame["action"] if ('action' in frame) else -1,
                   "scheduled_actions": frame["plan"]["scheduled_actions"] if ('plan' in frame) else -1,
                   "cum_return": frame["cum_return"],
                   "incr_return": frame["incr_return"],
                   "current_time": frame["state"]["current_time"],
                   "cat": frame["state"]["cat"],
                   "orders": frame["state"]["orders"],
                   "scheduled_event_queue": frame["state"]["scheduled_event_queue"],
                   "foresight_order_buffer": frame["state"]["foresight_order_buffer"],
                   "decision_order_id": frame["state"]["decision_order_id"],
                   "total_lost": frame["state"]["total_lost"],
                   "total_waiting_cost": frame["state"]["total_waiting_cost"],
                   "total_lost_sale_cost": frame["state"]["total_lost_sale_cost"],
                   "OH": frame["state"]["OH"],
                   "IT": frame["state"]["IT"],
                   "index": index,
                   "configs": configs,
                   "total_frames": len(frames)
                   })

def open_browser():
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()


if __name__ == '__main__':
    open_browser()
    socketio.run(app, debug=True)
        
sys.stdout.flush()
#endregion
