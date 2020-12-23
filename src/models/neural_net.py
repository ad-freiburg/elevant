import torch


class NeuralNet(torch.nn.Module):
    def __init__(self, in_size, hidden_size, out_size, dropout=0.5):
        super(NeuralNet, self).__init__()
        self.l1 = torch.nn.Linear(in_size, hidden_size)
        self.dropout1 = torch.nn.Dropout(dropout)
        self.sigmoid1 = torch.nn.Sigmoid()
        self.l2 = torch.nn.Linear(hidden_size, out_size)
        self.dropout2 = torch.nn.Dropout(dropout)
        self.sigmoid2 = torch.nn.Sigmoid()

    def forward(self, x):
        out = self.l1(x)
        out = self.dropout1(out)
        out = self.sigmoid1(out)
        out = self.l2(out)
        out = self.dropout2(out)
        out = self.sigmoid2(out)
        return out
