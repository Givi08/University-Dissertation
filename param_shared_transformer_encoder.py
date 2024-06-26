from torch import nn
#from encoders import Encoder
import torch

class ParameterSharedTransformerEncoder(nn.TransformerEncoder):
    def __init__(self,
                d_model: int = 512,
                nhead: int = 4,
                dim_feedforward: int = 2048,
                dropout: float = 0.1,
                activation = "relu",
                num_unique_layers: int = 4,
                num_total_layers: int = 8,
                mode = "cycle_rev",
                norm: bool = False,):

        # Checking method here
        assert mode in {"sequence", "cycle", "cycle_rev"}
        quotient, remainder = divmod(num_total_layers, num_unique_layers)
        assert remainder == 0
        if mode == "cycle_rev":
            assert quotient == 2

        # create encoder layer
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, 
                                                    dim_feedforward, dropout, activation)
        
        super().__init__(encoder_layer, 
                         num_layers=num_unique_layers, 
                         norm=norm)
        
        self.N = num_total_layers
        self.M = num_unique_layers
        self.mode = mode
        self.norm = nn.LayerNorm(d_model) if norm else None

    def forward(self, x, mask=None, src_key_padding_mask=None, verbose=True):

        mask = mask.to(torch.float)
        #src_key_padding_mask = torch.reshape(src_key_padding_mask, (5,12))
        #print(src_key_padding_mask.shape)
        
        for i in range(self.N):
            if self.mode == "sequence":
                i = i // (self.N // self.M)
            elif self.mode == "cycle":
                i = i % self.M
            elif i > (self.N - 1) / 2:
                i = self.N - i - 1
            if verbose:
                print(f"layer {i}")

            x = self.layers[i](x, None)
        if self.norm is not None:
            x = self.norm(x)
        return x
