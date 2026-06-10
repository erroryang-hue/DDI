import torch
import torch.nn.functional as F

from torch_geometric.nn import SAGEConv


class DDI_GNN(torch.nn.Module):

    def __init__(
        self,
        in_channels,
        hidden_channels
    ):
        super().__init__()

        self.conv1 = SAGEConv(
            in_channels,
            hidden_channels
        )

        self.conv2 = SAGEConv(
            hidden_channels,
            hidden_channels
        )
        # predictor head: combines pair features
        self.pred = torch.nn.Sequential(
            torch.nn.Linear(hidden_channels * 4, hidden_channels),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_channels, 1),
        )

    def encode(
        self,
        x,
        edge_index
    ):

        x = self.conv1(
            x,
            edge_index
        )

        x = F.relu(x)

        x = self.conv2(
            x,
            edge_index
        )

        return x

    def predict(
        self,
        z,
        src,
        dst
    ):
        # construct pair features: z_u, z_v, z_u * z_v, |z_u - z_v|
        zu = z[src]
        zv = z[dst]
        pair = torch.cat([zu, zv, zu * zv, torch.abs(zu - zv)], dim=1)
        return self.pred(pair).squeeze(-1)