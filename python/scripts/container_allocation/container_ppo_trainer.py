#region header
from enum import Enum
import numpy as np
import json5
import os, time, sys
from dp import dynaplex

from dp.utils.tianshou.network_wrapper import TianshouModuleWrapper
from dp.gym.base_env import BaseEnv
import tianshou as ts
from tianshou.utils import TensorboardLogger
import torch
from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import ExponentialLR
print(sys.path)
from scripts.networks.lost_sales_actor_critic_mlp import CriticMLP, ActorMLP
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
#endregion

def policy_path():
    path = os.path.normpath(dynaplex.filepath(mdp.identifier(),"policies",  "ppo_policy"))
    return path

def save_best_fn(policy):
    save_path = policy_path()
    dynaplex.save_policy(policy.actor.wrapped_module,
                   {'input_type': 'dict', 'num_inputs': mdp.num_flat_features(), 'num_outputs': mdp.num_valid_actions(), 'id': 'ppo-run2' },
                   save_path)

def get_env():
    return BaseEnv(mdp, train_args["num_actions_until_done"])

def get_test_env():    
    return BaseEnv(mdp, train_args["num_steps_per_test_episode"])

def preprocess_function(**kwargs):
    """
    Observations contain the mask as part of a dictionary.
    This function ensures that the data gathered in training and testing are in the correct format.
    """
    if "obs" in kwargs:
        obs_with_tensors = [
            {"obs": torch.from_numpy(obs['obs']).to(torch.float).to(device=device),
             "mask": torch.from_numpy(obs['mask']).to(torch.bool).to(device=device)}
            for obs in kwargs["obs"]]
        kwargs["obs"] = obs_with_tensors
    if "obs_next" in kwargs:
        obs_with_tensors = [
            {"obs": torch.from_numpy(obs['obs']).to(torch.float).to(device=device),
             "mask": torch.from_numpy(obs['mask']).to(torch.bool).to(device=device)}
            for obs in kwargs["obs_next"]]
        kwargs["obs_next"] = obs_with_tensors
    return kwargs

# Training parameters
train_args = {"hidden_dim": 128,
              "lr": 1e-3,
              "discount_factor": 1.0, #0.99
              "batch_size": 32,         # Sample size
              "max_batch_size": 0,      # 0 means step_per_collect amount
              "nr_train_envs": 8,
              "nr_test_envs": 4,
              "step_per_collect": 512,  # 'Population' size for sampling
              "step_per_epoch": 16384,
              "max_epoch": 20,
              "repeat_per_collect": 2,
              "replay_buffer_size": 1024,
              "max_batchsize": 2048,
              "num_actions_until_done": 0,   # train environments can be either infinite or finite horizon mdp. 0 means infinite horizon
              "num_steps_per_test_episode": 5000    # in order to use test environments, episodes should be guaranteed to get to terminations
              }

comparer_config = {"number_of_trajectories": 100,
                   "periods_per_trajectory": 10000,
                   "rng_seed": 324324,
                   "number_of_statistics": 5 + 3 * 4,
                   "print_standard_error": True
                   }

if __name__ == '__main__':
    for alpha in [25, 60]:      # Prem. order rate
        for gamma in [60, 80]:  # Cent. depot outflow rate
            beta = 50           # Special container rate
            C = 10              # Number of containers
            configs.update({"lost_sale_M": 1e10})   # Lost sale big M
            #region ConfigureProblem
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
            type_labels = ["Special","Generic"]
            dist_frac = [
                [C * (100-gamma) / 200 * beta/100, C * (100-gamma) / 200 * (100-beta) / 100],
                [C * gamma/100 * beta/100, C * gamma/100 * (100-beta)/100],
                [C * (100-gamma) / 200 * beta/100, C * (100-gamma) / 200 * (100-beta) / 100]
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
            configs.update({"initial_containers": initial_containers});
            #endregion
            mdp = dynaplex.get_mdp(**configs)
            train = True
            if train:
                model_name = "ppo_model_dict.pt"     #used for tensorboard logging
                device = "cuda" if torch.cuda.is_available() else "cpu"
                print(f'Device is {device}')
                # define actor network structure
                actor_net = ActorMLP(
                    input_dim=mdp.num_flat_features(),
                    hidden_dim=train_args["hidden_dim"],
                    output_dim=mdp.num_valid_actions(),
                    min_val=torch.finfo(torch.float).min
                ).to(device)

                # define critic network structure
                critic_net = CriticMLP(
                    input_dim=mdp.num_flat_features(),
                    hidden_dim=train_args["hidden_dim"],
                    output_dim=mdp.num_valid_actions(),
                    min_val=torch.finfo(torch.float).min
                ).to(device).share_memory()

                # define optimizer
                optim = torch.optim.Adam(
                    params=list(actor_net.parameters()) + list(critic_net.parameters()),
                    lr=train_args["lr"]
                )

                # define scheduler
                scheduler = ExponentialLR(optim, 0.99)

                # define PPO policy
                policy = ts.policy.PPOPolicy(TianshouModuleWrapper(actor_net), critic_net, optim,
                                            discount_factor=train_args["discount_factor"],
                                            max_batchsize=train_args["max_batchsize"], # max batch size for GAE estimation, default to 256
                                            value_clip=True,
                                            dist_fn=torch.distributions.categorical.Categorical, # Emprical distribution matching the output vector, insignificant
                                            deterministic_eval=False,   #True,
                                            lr_scheduler=scheduler,
                                            reward_normalization=False
                                            )
                policy.action_type = "discrete"

                # a tensorboard logger is available to monitor training results.
                # log in the directory where all mdp results are stored:
                log_path = dynaplex.filepath(mdp.identifier(), "tensorboard_logs", model_name)
                writer = SummaryWriter(log_path)
                logger = TensorboardLogger(writer)

                # create nr_envs train environments
                train_envs = ts.env.DummyVectorEnv(
                    [get_env for _ in range(train_args["nr_train_envs"])]
                )
                collector = ts.data.Collector(policy, train_envs, ts.data.VectorReplayBuffer(train_args["replay_buffer_size"], train_args["nr_train_envs"]), exploration_noise=True, preprocess_fn=preprocess_function)
                collector.reset()

                # create nr_envs test environments
                test_envs = ts.env.DummyVectorEnv(
                    [get_test_env for _ in range(train_args["nr_test_envs"])]
                )
                test_collector = ts.data.Collector(policy, test_envs, exploration_noise=False, preprocess_fn=preprocess_function)
                test_collector.reset()

                # train the policy
                print("Starting training")
                start = time.time()
                policy.train()
                trainer = ts.trainer.OnpolicyTrainer(
                    policy, collector, test_collector=test_collector,
                    # policy, collector, test_collector=None,
                    max_epoch=train_args["max_epoch"],
                    step_per_epoch=train_args["step_per_epoch"],
                    step_per_collect=train_args["step_per_collect"],
                    episode_per_test=10, batch_size=train_args["batch_size"],
                    repeat_per_collect=train_args["repeat_per_collect"],
                    logger=logger, test_in_train=True,
                    save_best_fn=save_best_fn)
                print(f'save location:{policy_path()}')
                result = trainer.run()
                print(f"Finished training in {time.time()-start} sec's!")
                print("Training finished")

            policies = [dynaplex.load_policy(mdp, policy_path()), mdp.get_policy(id = "NearestDepotRandomized", p_rand = 0.0)]
            comparer = dynaplex.get_comparer(mdp, **comparer_config)

            comparison = comparer.compare(policies)
            for item in comparison:
                print(item)
            print("Testing finished")