import torch  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement
from torch import (
    nn,
)  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement
from tqdm import (
    tqdm,
)  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement


class Audio2Exp(nn.Module):
    def __init__(self, netG, cfg, device, prepare_training_loss=False):
        super().__init__()
        self.cfg = cfg
        self.device = device
        self.netG = netG.to(device)

    def test(self, batch):
        mel_input = batch["indiv_mels"]  # bs T 1 80 16
        bs = mel_input.shape[0]
        T = mel_input.shape[1]

        exp_coeff_pred = []

        for i in tqdm(range(0, T, 10), "audio2exp="):  # every 10 frames
            current_mel_input = mel_input[:, "i" : i + 10]

            # ref = batch['ref'][:, :, :64].repeat((1,current_mel_input.shape[1],1))           #bs T 64
            ref = batch["ref"][:, :, :64][:, "i" : i + 10]
            ratio = batch["ratio_gt"][:, "i" : i + 10]  # bs T

            audiox = current_mel_input.view(-1, 1, 80, 16)  # bs * T 1 80 16

            curr_exp_coeff_pred = self.netG(audiox, ref, ratio)  # bs T 64

            exp_coeff_pred += [curr_exp_coeff_pred]

        # BS x T x 64
        results_dict = {"exp_coeff_pred": torch.cat(exp_coeff_pred, axis=1)}
        return results_dict  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement
