from torch import nn
from torch.nn import functional as F
import torch
from torch_geometric.nn import GCNConv

class TemporalGNN(nn.Module):
    def __init__(self, input_dim=165, hidden_dim=64, dropout=0.3):
        super().__init__()
        self.gcn1 = GCNConv(input_dim, hidden_dim, cached=False)
        self.gcn2 = GCNConv(hidden_dim, hidden_dim, cached=False)
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        self.classifier = nn.Linear(2 * hidden_dim, 2)
        self.dropout = dropout

    def forward(self, x, edge_index, memory=None):
        z = F.relu(self.gcn1(x, edge_index))
        z = F.dropout(z, p=self.dropout, training=self.training)
        z = F.relu(self.gcn2(z, edge_index))
        graph_summary = z.mean(dim=0, keepdim=True)
        if memory is None:
            memory = torch.zeros_like(graph_summary)
        memory = self.gru(graph_summary, memory)
        combined = torch.cat([z, memory.expand(z.shape[0], -1)], dim=1)
        return self.classifier(combined), memory
