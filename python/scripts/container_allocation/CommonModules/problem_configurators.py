from dp import dynaplex
import json5

def ConfigureProblem(configs, alpha, beta, gamma, C = 10, lost_sale_M = 0, lmbda = 0.008004):
    """
    Reconfigures the configuration with the provided hyper-parameters.

    Args:
        configs(dict):Problem configuration dictionary.
        alpha (float): Premium requests rate.
        beta (float): Special container percentage.
        gamma (float): Geographical imbalance parameter.
        C (float, optional): Number of containers. Defaults to 10.
        lost_sale_M (float, optional): Artificial lost sale cost for training. Defaults to 0.
        lmbda (float, optional): Arrival rate. Low = 0.004002, Regular = 0.008004, High = 0.040020

    Returns:
        dict: Modified configs for container allocation problem.
    """
    configs["lost_sale_M"] = lost_sale_M
    configs["pooled_arrival_rate"] = lmbda
    new_order_types = [{
        "key": "Premium",
        "arrival_rate": alpha,
        "container_type_options": ["Special"]
        },
        {
        "key": "Regular",
        "arrival_rate": 100-alpha,
        "container_type_options": ["Generic", "Special"]
        }
        ]
    configs.update({"order_types": new_order_types})

    new_lanes = [{
        "o_key": "Center",
        "d_key": "North",
        "weight": gamma/2
        },
        {
        "o_key": "Center",
        "d_key": "South",
        "weight": gamma/2
        },
        {
        "o_key": "North",
        "d_key": "Center",
        "weight": (100-gamma)/2
        },
        {
        "o_key": "South",
        "d_key": "Center",
        "weight": (100-gamma)/2
        }
        ]
    configs.update({"order_lanes": new_lanes})

    initial_containers = []
    depot_labels = ["North","Center","South"]
    type_labels = ["Special", "Generic"]
    C_generic = int(C * (1 - beta / 100))
    dist_per_types = [ C - C_generic, C_generic ]
    normalized_dist_per_depots = [ (100 - gamma) / 200, gamma / 100, (100 - gamma) / 200 ]

    for i in range(len(type_labels)):
        allocated = [0 for _ in range(len(depot_labels))]
        total_allocated = 0
        remaining_containers = dist_per_types[i]
        fractional_dist = [remaining_containers * normalized_dist_per_depots[0],
                           remaining_containers * normalized_dist_per_depots[1],
                           remaining_containers * normalized_dist_per_depots[2]]

        for j in range(len(depot_labels)):
            while allocated[j]+1 <= fractional_dist[j]:
                allocated[j] += 1
                total_allocated += 1
                remaining_containers -= 1
                initial_containers += [{
                    "type_key": type_labels[i],
                    "depot_key": depot_labels[j],
                    "release_times": 4*[0]
                }]

        remainder_fracs = []
        for j in range(len(depot_labels)):
            remainder_fracs += [[fractional_dist[j] - allocated[j], i, j]]
        remainder_fracs.sort(reverse=True)

        for k in range(remaining_containers):
            _, i, j = remainder_fracs[k]
            initial_containers += [{
                "type_key": type_labels[i],
                "depot_key": depot_labels[j],
                "release_times": 4*[0]
            }]
    configs.update({"initial_containers": initial_containers})

def ConfigureProblemSingleType(configs, gamma, C, lost_sale_M = 0, lmbda = 0.008004):
    """
    Reconfigures the configuration with the provided hyper-parameters.

    Args:
        configs(dict):Problem configuration dictionary.
        gamma (float): Geographical imbalance parameter.
        C (float, optional): Number of containers. Defaults to 10.
        lost_sale_M (float, optional): Artificial lost sale cost for training. Defaults to 0.
        lmbda (float, optional): Arrival rate. low: 0.004002, regular: 0.008004, high: 0.040020

    Returns:
        dict: Modified configs for container allocation problem.
    """
    configs["num_initial_containers"] = C
    configs["lost_sale_M"] = lost_sale_M
    configs["pooled_arrival_rate"] = lmbda
    new_order_types = [{
        "key": "Premium",
        "arrival_rate": 100,
        "container_type_options": ["Generic"]
        }
        ]
    configs.update({"order_types": new_order_types})

    new_lanes = [{
        "o_key": "Center",
        "d_key": "North",
        "weight": gamma/2
        },
        {
        "o_key": "Center",
        "d_key": "South",
        "weight": gamma/2
        },
        {
        "o_key": "North",
        "d_key": "Center",
        "weight": (100-gamma)/2
        },
        {
        "o_key": "South",
        "d_key": "Center",
        "weight": (100-gamma)/2
        }
        ]
    configs.update({"order_lanes": new_lanes})

    initial_containers = []
    depot_labels = ["North","Center","South"]
    type_labels = ["Generic"]
    dist_frac = [
        [C * (100-gamma) / 200 ],
        [C * gamma/100 ],
        [C * (100-gamma) / 200]
    ]
    allocated = [[0 for _ in range(len(type_labels))] for __ in range(len(depot_labels))]
    total_allocated = 0
    remaining_containers = C
    for i in range(len(depot_labels)):
        for j in range(len(type_labels)):
            while allocated[i][j]+1 <= dist_frac[i][j]:
                allocated[i][j] += 1
                total_allocated += 1
                remaining_containers -= 1
                initial_containers += [{
                    "type_key": type_labels[j],
                    "depot_key": depot_labels[i],
                    "release_times": 4*[0]
                }]

    remainder_fracs = []
    for i in range(len(depot_labels)):
        for j in range(len(type_labels)):
            remainder_fracs += [[dist_frac[i][j] - allocated[i][j], i, j]]
    remainder_fracs.sort(reverse=True)

    for k in range(remaining_containers):
        _, i, j = remainder_fracs[k]
        initial_containers += [{
            "type_key": type_labels[j],
            "depot_key": depot_labels[i],
            "release_times": 4*[0]
        }]
    configs.update({"initial_containers": initial_containers})

def GetMDPConfigFile(folder_name = "container_allocation", mdp_version = 2, mdp_version_additional_setting = "" ):
    path_to_json = dynaplex.filepath("mdp_config_examples", folder_name, "config_files/" + f"mdp_config_{mdp_version}" + mdp_version_additional_setting + ".json")
    try:
        with open(path_to_json, "r") as input_file:
            return json5.load(input_file)    # configs can be initialized manually with something like
    except FileNotFoundError:
        raise FileNotFoundError(f"File {path_to_json} not found. Please make sure the file exists and try again.")
    except:
        raise Exception("Something went wrong when loading the json file. Have you checked the json file does not contain any comment?")

def GetPolicyConfigFile(folder_name = "container_allocation", policy_version = 2, policy_version_additional_setting = "" ):
    path_to_json = dynaplex.filepath("mdp_config_examples", folder_name, "config_files\\\\" + f"policy_config_{policy_version}" + policy_version_additional_setting + ".json")
    try:
        with open(path_to_json, "r") as input_file:
            return json5.load(input_file)    # configs can be initialized manually with something like
    except FileNotFoundError:
        raise FileNotFoundError(f"File {path_to_json} not found. Please make sure the file exists and try again.")
    except:
        raise Exception("Something went wrong when loading the json file. Have you checked the json file does not contain any comment?")

def UpdateIOPath(path_relative_to_root):
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(script_dir, "../../../..")
    io_path = os.path.abspath(os.path.join(root_dir, path_relative_to_root))
    dynaplex.set_io_path(io_path)