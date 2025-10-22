from dp import dynaplex
import json5
from CommonModules.problem_configurators import *

#region Dynaplex data
folder_name = "container_allocation"
mdp_version_number = 2
mdp_version_additional_setting = "_no_DD"
path_to_json = dynaplex.filepath("mdp_config_examples", folder_name, f"mdp_config_{mdp_version_number}" + mdp_version_additional_setting + ".json")
configs = GetMDPConfigFile(folder_name = "container_allocation", mdp_version = "dh_2", mdp_version_additional_setting = "")
#endregion

def dcl_policy(gen):
    dcl_filename = f'dcl_python_{gen}'
    dcl_load_path = dynaplex.filepath(mdp.identifier(), "dcl_python", dcl_filename)
    return dynaplex.load_policy(mdp, dcl_load_path)
def ppo_policy():
    ppo_filename = 'ppo_policy'
    ppo_load_path = dynaplex.filepath(mdp.identifier(), "policies", ppo_filename)
    return dynaplex.load_policy(mdp, ppo_load_path)

mdp = dynaplex.get_mdp(**configs)
rand_policy = mdp.get_policy("random")
heur_gwd = mdp.get_policy(id="DelayAlways")

policies = [rand_policy, heur_gwd]

comparer = dynaplex.get_comparer(mdp, number_of_trajectories=10, periods_per_trajectory=10, warmup_periods=0)
comparison = comparer.compare(policies)
result = [(item['policy']['id'], item['mean'], item['st_error']) for item in comparison]

print(result)