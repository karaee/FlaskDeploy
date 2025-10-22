from typing import Dict

import torch
from torch.nn import Linear, ReLU, Sequential, LayerNorm, Tanh


class ActorMLP(torch.nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim, min_val=torch.finfo(torch.float).min, activation=ReLU):
        super(ActorMLP, self).__init__()
        self.min_val = min_val
        self.output_dim = output_dim
        self.max_action = None

        self.actor = Sequential(
            Linear(input_dim, hidden_dim),
            activation(),
            Linear(hidden_dim, hidden_dim),
            activation(),
            Linear(hidden_dim, hidden_dim),
            activation(),
            Linear(hidden_dim, output_dim)
        )
        self.softmax = torch.nn.Softmax(dim=1)

        self.state_scale_list = []
        for i in range(0, 6):
            self.state_scale_list.append(4) #demand
            self.state_scale_list.append(1) # deviation
            self.state_scale_list.append(15*4) # inventory
            self.state_scale_list.append(22) # production quantity
            self.state_scale_list.append(1.0) # setup
        self.state_scale_list.append(22)
        self.scaling_tensor = torch.tensor(self.state_scale_list, dtype = torch.float)
        

    # Dict input
    def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:

        x = observations['obs'] / self.scaling_tensor
        x = self.actor(x)
        x = torch.clamp(x, min = -1, max=1)

        #if we are in inference mode, mask is optional:
        if observations.get('mask') is not None:
            action_masks = observations['mask']
            x[~action_masks] = self.min_val
            x = self.softmax(x)
        #since mask is not needed in inference mode, the `input_type` of this network should be `dict', i.e.
        #this key and value must be included in the json when saving. 
        #if mask were mandatory, e.g. if it is needed to make inference faster by avoiding the forwarding of certain nodes,
        #then `input_type' should be `dict_with_mask'.
        return x


class CriticMLP(torch.nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim, min_val=torch.finfo(torch.float).min, activation=ReLU):
        super(CriticMLP, self).__init__()
        self.min_val = min_val
        self.output_dim = output_dim
        self.critic = Sequential(
            Linear(input_dim, hidden_dim),
            activation(),
            Linear(hidden_dim, hidden_dim),
            activation(),
            Linear(hidden_dim, hidden_dim),
            activation(),
            Linear(hidden_dim, 1)
        )

        self.state_scale_list = []
        for i in range(0, 6):
            self.state_scale_list.append(4) #demand
            self.state_scale_list.append(1) # deviation
            self.state_scale_list.append(15*4) # inventory
            self.state_scale_list.append(22) # production quantity
            self.state_scale_list.append(1.0) # setup
        self.state_scale_list.append(22)
        self.scaling_tensor = torch.tensor(self.state_scale_list, dtype = torch.float)

        

    def forward(self, observations, state=None, info={}):

        action_masks = observations['mask']
        batch_data = observations['obs']

        x = batch_data.clone().detach() / self.scaling_tensor
        x = torch.clamp(x, min = -1, max=1)
        #torch.tensor(batch_data, dtype=torch.float)
        x = self.critic(x)
        return x
