from typing import Dict

import torch
from torch.nn import Linear, ReLU, Sequential, LayerNorm


class ActorMLP(torch.nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim, min_val=torch.finfo(torch.float).min, activation=ReLU):
        super(ActorMLP, self).__init__()
        self.min_val = min_val

        self.n_pickers = 4
        self.n_picker_features = 5

        self.n_vehicles = 7
        self.n_vehicle_features = 6

        self.picker_embedding = Sequential(
            Linear(self.n_picker_features, hidden_dim),
            LayerNorm(hidden_dim),
            activation(),
        )

        self.vehicle_embedding = Sequential(
            Linear(self.n_vehicle_features, hidden_dim),
            LayerNorm(hidden_dim),
            activation(),
        )

        self.decoder_1 = Linear(hidden_dim * 2, hidden_dim)
        self.decoder_out = Linear(hidden_dim, 1)

        self.softmax = torch.nn.Softmax(dim=1)

    # Dict input
    def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:

        batch_size = observations['obs'].shape[0]
        current_picker = observations['obs'][:, 0].to(torch.int32)

        x_pickers = observations['obs'][:, 1:self.n_picker_features*self.n_pickers+1].reshape(-1, self.n_pickers, self.n_picker_features)
        x_vehicles = observations['obs'][:, self.n_picker_features*self.n_pickers+1:].reshape(-1, self.n_vehicles, self.n_vehicle_features)

        x_pickers = self.picker_embedding(x_pickers)

        x_vehicles = self.vehicle_embedding(x_vehicles)

        origin_picker = x_pickers[torch.arange(batch_size), current_picker].unsqueeze(1)

        x_dest = torch.cat((x_vehicles, origin_picker), dim=1)
        x_origin = origin_picker.repeat(1, self.n_vehicles + 1, 1)

        x = torch.cat((x_origin, x_dest), dim=2)

        x = self.decoder_1(x).relu()
        x = self.decoder_out(x).squeeze(-1)

        # if we are in inference mode, mask is optional:
        if observations.get('mask') is not None:
            action_masks = observations['mask']
            x[~action_masks] = self.min_val
            x = self.softmax(x)

        return x


class CriticMLP(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, min_val=torch.finfo(torch.float).min, activation=ReLU):
        super(CriticMLP, self).__init__()
        self.n_pickers = 4
        self.n_picker_features = 5

        self.n_vehicles = 7
        self.n_vehicle_features = 6

        self.picker_embedding = Sequential(
            Linear(self.n_picker_features, hidden_dim),
            LayerNorm(hidden_dim),
            activation(),
        )

        self.vehicle_embedding = Sequential(
            Linear(self.n_vehicle_features, hidden_dim),
            LayerNorm(hidden_dim),
            activation(),
        )

        self.decoder_1 = Linear(hidden_dim * 2, hidden_dim)
        self.decoder_out = Linear(hidden_dim, 1)

    def forward(self, observations, state=None, info={}):
        batch_size = observations['obs'].shape[0]
        current_picker = observations['obs'][:, 0].to(torch.int32)

        x_pickers = observations['obs'][:, 1:self.n_picker_features*self.n_pickers+1].reshape(-1, self.n_pickers, self.n_picker_features)
        x_vehicles = observations['obs'][:, self.n_picker_features*self.n_pickers+1:].reshape(-1, self.n_vehicles, self.n_vehicle_features)

        x_pickers = self.picker_embedding(x_pickers)

        x_vehicles = self.vehicle_embedding(x_vehicles)

        origin_picker = x_pickers[torch.arange(batch_size), current_picker].unsqueeze(1)

        x_dest = torch.cat((x_vehicles, origin_picker), dim=1)
        x_origin = origin_picker.repeat(1, self.n_vehicles + 1, 1)

        x = torch.cat((x_origin, x_dest), dim=2)

        x = self.decoder_1(x).relu()
        x = self.decoder_out(x).squeeze()

        x = x.mean(dim=1)

        return x
