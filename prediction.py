
import numpy as np
import math
import sys
import pickle

import torch
from torchtext.data import Dataset

from plot_videos import alter_DTW_timing
from helpers import bpe_postprocess, load_config, get_latest_checkpoint, \
    load_checkpoint, calculate_dtw, calculate_pck
from model import build_model, Model
from batch import Batch
from data import load_data, make_data_iter
from constants import UNK_TOKEN, PAD_TOKEN, EOS_TOKEN

# Validate epoch given a dataset
def validate_on_data(model: Model,
                     data: Dataset,
                     batch_size: int,
                     max_output_length: int,
                     eval_metric: str,
                     loss_function: torch.nn.Module = None,
                     batch_type: str = "sentence",
                     type = "val",
                     BT_model = None):

    valid_iter = make_data_iter(
        dataset=data, batch_size=batch_size, batch_type=batch_type,
        shuffle=True, train=False)

    pad_index = model.src_vocab.stoi[PAD_TOKEN]
    # disable dropout
    model.eval()
    # don't track gradients during validation
    with torch.no_grad():
        valid_hypotheses = []
        valid_references = []
        valid_inputs = []
        file_paths = []
        all_dtw_scores = []
        all_pcks = []

        valid_loss = 0
        total_ntokens = 0
        total_nseqs = 0

        batches = 0
        for valid_batch in iter(valid_iter):
            # Extract batch
            batch = Batch(torch_batch=valid_batch,
                          pad_index = pad_index,
                          model = model)
            targets = batch.trg

            # run as during training with teacher forcing
            if loss_function is not None and batch.trg is not None:
                # Get the loss for this batch
                batch_loss, _ = model.get_loss_for_batch(
                    batch, loss_function=loss_function)

                valid_loss += batch_loss
                total_ntokens += batch.ntokens
                total_nseqs += batch.nseqs   

            # If not just count in, run inference to produce translation videos
            if not model.just_count_in:
                # Run batch through the model in an auto-regressive format
                output, attention_scores = model.run_batch(
                                            batch=batch,
                                            max_output_length=max_output_length)
                # print(batch.src.shape)
                # print(batch.src_lengths)
                # print(batch.src_mask.shape)
                # print("-------")
                # print(batch.trg.shape)
                # print(batch.trg_input.shape)
                # print(batch.trg_lengths)
                # print(batch.trg_mask.shape)
                # print("-------")
                # print(output.shape)
                # print(output[0][0])
                # print("")
                # print(output[1][0])
                # sys.exit()


            # If future prediction
            if model.future_prediction != 0:
                # Cut to only the first frame prediction + add the counter
                targets = torch.cat((targets[:, :, :targets.shape[2] // (model.future_prediction)], targets[:, :, -1:]),dim=2)
            # Add references, hypotheses and file paths to list
            valid_references.extend(targets)
            valid_hypotheses.extend(output)
            file_paths.extend(batch.file_paths)
            # Add the source sentences to list, by using the model source vocab and batch indices
            valid_inputs.extend([[model.src_vocab.itos[batch.src[i][j]] for j in range(len(batch.src[i]))] for i in
                                 range(len(batch.src))])

            # Calculate the full Dynamic Time Warping score - for evaluation
            dtw_score = calculate_dtw(targets, output)
            all_dtw_scores.extend(dtw_score)
            # print(output.shape)
            # print(targets.shape)
            # with open("output.txt", "wb") as f:
            #     pickle.dump(output[8], f)
            # with open("target.txt", "wb") as f:
            #     pickle.dump(targets[8], f)
            for b in range(output.shape[0]):
                hyp, ref, _ = alter_DTW_timing(output[b], targets[b])
                pck = calculate_pck(hyp[:,:-1], ref[:,:-1])
                all_pcks.append(np.mean(pck))
            
            # print(all_dtw_scores)
            # print(all_pcks)
            # print(all_dtw_scores[8])
            # print(all_pcks[8])
            # print(batch.src[8])
            # print(valid_inputs[8])

            # sys.exit()
            # Can set to only run a few batches
            # if batches == math.ceil(20/batch_size):
            #     break
            batches += 1

        # Dynamic Time Warping scores
        current_valid_score = np.mean(all_dtw_scores)

    return current_valid_score, valid_loss/batches, valid_references, valid_hypotheses, \
           valid_inputs, all_dtw_scores, file_paths, all_pcks