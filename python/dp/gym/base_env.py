import os
import sys

import numpy as np
import gymnasium as gym

from gymnasium import spaces
from gymnasium.utils import seeding

from dp import dynaplex

# The BaseEnv class extends the basic gymnasium AECEnv class to interact with a Dynaplex MDP
class BaseEnv(gym.Env):

    metadata = {"render_modes": ["human"]}

    def __init__(self, mdp, num_actions_until_done=0, num_periods_until_done=0, **kwargs):
        # Emulator holds the current state of the mdp
        self.emulator = dynaplex.get_gym_emulator(mdp=mdp, num_actions_until_done=num_actions_until_done,
                                            num_periods_until_done=num_periods_until_done)

        # Observations are a dictionary containing a Box (a vector of length self.emulator.observation_space_size())
        # which can contain unbounded values, and the action mask
        self.observation_space = spaces.Dict({'obs': spaces.Box(low=-float('inf'), high=float('inf'), shape=(self.emulator.observation_space_size(),), dtype=float),
                                              'mask': spaces.MultiBinary(self.emulator.action_space_size())})

        # Actions are always discrete
        self.action_space = spaces.Discrete(self.emulator.action_space_size())

    def reset(self, seed=None):
        # Manage random seeding like a normal gym env
        if seed is None:
            generator, _ = seeding.np_random()
            seed_gen = generator.integers(0, np.iinfo(np.int32).max, dtype=np.int64)
            seed = seed_gen.item()

        # Get initial state from dp MDP
        observation, info = self.emulator.reset(seed=seed)  # get_initial_state resets the dp emulator and returns the initial state

        return {'obs': np.asarray(observation[0]), 'mask': np.asarray(observation[1])}, {}  # second return value is empty info

    def step(self, action):
        """
        Step gets an action and calls the Dynaplex mdp step function, which evolves the simulation until another action is required.
        """
        observation, reward, terminated, truncated, info = self.emulator.step(action)

        return (
            {'obs': np.asarray(observation[0]), 'mask': np.asarray(observation[1])},
            reward,
            terminated,
            truncated,
            {'info': info}
        )

    def render(self):
        raise NotImplementedError
