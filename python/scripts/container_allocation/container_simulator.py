#region header
import json5
from dp import dynaplex
import os, pickle, time
from enum import Enum

colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#1f77b4', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896',
    '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d',
    '#9edae5' 
]
ContainerStatus = Enum('ContainerStatus', [('Idle', 0), ('ToOrigin', 1), ('ToDestination', 2), ('ToDepot', 3)])
#endregion
#region Get mdp data
folder_name = "container_allocation"
mdp_version_number = 2
path_to_json = dynaplex.filepath("mdp_config_examples", folder_name, f"mdp_config_{mdp_version_number}.json")
try:
    with open(path_to_json, "r") as input_file:
        configs = json5.load(input_file)    # configs can be initialized manually with something like
except FileNotFoundError:
    raise FileNotFoundError(f"File {path_to_json} not found. Please make sure the file exists and try again.")
except:
    raise Exception("Something went wrong when loading the json file. Have you checked the json file does not contain any comment?")

mdp = dynaplex.get_mdp(**configs)
#endregion

# policy_name = "DelayAlways"
# policy_name = "random"
# policy_name = "GreedyPolicyWithDelayLex"
# policy = mdp.get_policy(policy_name)

policy_name = "ppo_policy"
policy_path = os.path.normpath(dynaplex.filepath(mdp.identifier(), "policies", policy_name))
policy = dynaplex.load_policy(mdp, policy_path)

seed = 324324
demonstrator = dynaplex.get_demonstrator(max_period_count= 500, rng_seed = seed)
trace = demonstrator.get_trace(mdp, policy)
path = dynaplex.filepath(mdp.identifier(), "rollouts",  policy_name + str(seed) + ".pkl")
print(path)
start = time.time()
with open(path, 'wb') as f:
    pickle.dump(trace, f, protocol=pickle.HIGHEST_PROTOCOL)

print(f"Saved to {path} in {time.time()-start} sec's!")