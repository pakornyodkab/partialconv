import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .utils import save_ckpt
from .evaluate import evaluate


class Trainer:
    def __init__(self, step, config, device, model, dataset_train,
                 dataset_val, criterion, optimizer, experiment):
        self.stepped = step
        self.config = config
        self.device = device
        self.model = model
        self.dataloader_train = DataLoader(dataset_train,
                                           batch_size=config.batch_size,
                                           shuffle=True)
        self.dataset_val = dataset_val
        self.criterion = criterion
        self.optimizer = optimizer
        self.evaluate = evaluate
        self.experiment = experiment
        
    def iterate(self, num_iter):
        print('Start the training')
        for step, (input, mask, gt) in enumerate(self.dataloader_train):
            loss_dict, loss = train(step+self.stepped, input, mask, gt)
            # report the loss
            if step % self.config.print_interval == 0:
                self.report_loss(step+self.stepped, loss_dict, loss)

            # evaluation
            if (step+self.stepped + 1) % self.config.vis_interval == 0:
                # set the model to evaluation mode
                self.model.eval()
                self.evaluate(self.model, self.dataset_val, self.device,
                              '{}/train_out/test_{}.png'.format(self.config.ckpt, step+self.stepped),
                              self.experiment)

            # save the model
            if (step+self.stepped + 1) % self.config.save_model_interval == 0 \
                    or (i + 1) == self.config.max_iter:
                save_ckpt('{}/models/{}.pth'.format(self.config.ckpt, step+self.stepped + 1),
                          [('model', self.model)],
                          [('optimizer', self.optimizer)],
                          step+self.stepped + 1)

    def train(self, step, input, mask, gt):
        # set the model to training mode
        self.model.train()

        # send the input tensors to cuda
        input = input.to(device)
        mask = mask.to(device)
        gt = gt.to(device)

        # model forward
        output, _ = self.model(input, mask)
        loss_dict = self.criterion(input, mask, output, gt)
        loss = 0.0
        for key, coef in self.config.loss_coef.items():
            value = coef * loss_dict[key]
            loss += value

        # updates the model's params
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss_dict, loss
        
    def report(self, step, loss_dict, loss):
        # if self.experiment:
        #     experiment.log_metrics(
        print('STEP:', step,
              ' / Valid Loss:', loss_dict['valid'].item(),
              ' / Hole Loss:', loss_dict['hole'].item(),
              ' / TV Loss:', loss_dict['tv'].item(),
              ' / Perc Loss:', loss_dict['perc'].item(),
              ' / Style Loss:', loss_dict['style'].item(),
              ' / TOTAL LOSS:', loss.item())


