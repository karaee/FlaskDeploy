from typing import Dict

import torch
import torch.nn.functional as F
from torch.nn import Linear, ReLU, Sequential, LayerNorm, BatchNorm1d

# from time import time

class NodeMLPActor(torch.nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, n_nodes: int, min_val: float):

        super().__init__()

        self.n_nodes = n_nodes
        self.num_features = input_dim
        self.min_val = min_val

        self.lin1 = Linear(self.num_features, 2 * hidden_dim)
        # self.lin1 = Linear(self.num_features, hidden_dim)
        self.batch_norm = BatchNorm1d(2 * hidden_dim)
        # self.batch_norm = BatchNorm1d(hidden_dim)
        self.relu = ReLU()
        self.lin2 = Linear(2 * hidden_dim, hidden_dim)
        self.lin3 = Linear(hidden_dim, hidden_dim)
        self.lin4 = Linear(hidden_dim, 1)
        self.softmax = torch.nn.Softmax(dim=1)

    # def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:
    #
    #     # x = observations['obs'].reshape(-1, self.n_nodes, self.num_features)
    #
    #     n_nodes = int(observations['obs'].shape[1] / self.num_features)
    #     x = observations['obs'].reshape(-1, n_nodes, self.num_features)
    #
    #     batch_size = x.shape[0]
    #
    #     # The mask is always expected, even in inference mode to apply the decoder to fewer nodes
    #     action_masks = observations['mask'].to(torch.bool)
    #
    #     # out = torch.full((batch_size * self.n_nodes, 1), self.min_val)
    #     out = torch.full((batch_size * n_nodes, 1), self.min_val)
    #
    #     if not self.training:
    #         x = x[action_masks]
    #
    #     x = x.reshape(-1, self.num_features)
    #
    #     x = self.lin1(x)
    #     x = self.batch_norm(x)
    #     x = self.relu(x)
    #     x = F.dropout(x, p=0.2, training=self.training)
    #     x = self.lin2(x)
    #     x = self.relu(x)
    #     x = self.lin3(x)
    #
    #     if not self.training:
    #         action_masks = action_masks.flatten()
    #         out[action_masks] = x
    #         # x = out.reshape(-1, self.n_nodes)
    #         x = out.reshape(-1, n_nodes)
    #
    #     else:
    #         # x = x.reshape(-1, self.n_nodes)
    #         x = x.reshape(-1, n_nodes)
    #         # x[~action_masks] = self.min_val
    #
    #     # x = self.softmax(x)
    #
    #     return x

    def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:

        # reshape_start = time()

        n_nodes = observations['obs'].shape[1] // self.num_features
        x = observations['obs'].view(-1, self.num_features)  # More efficient reshape
        # action_masks = observations['mask'].to(torch.bool)

        x = self.lin1(x)
        # x = self.batch_norm(x)
        x = self.relu(x)

        # x = F.dropout(x, p=0.2, training=self.training)
        # x = F.dropout(x, p=0.2)
        x = self.lin2(x)
        x = self.relu(x)
        x = self.lin3(x)
        x = self.relu(x)
        x = self.lin4(x)

        x = x.view(-1, n_nodes)

        return x
