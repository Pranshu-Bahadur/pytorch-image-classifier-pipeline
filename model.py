import torch
from torch import functional as F
from torch import nn as nn
from torch.utils.tensorboard import SummaryWriter
import timm
from modules import Net
from sam import SAMSGD

class ImageClassifier(object):
    def __init__(self, config : dict):
        self.model = self._create_model(config["library"], config["model_name"], config["pretrained"], config["num_classes"])
        #if config["train"]:
        self.optimizer = self._create_optimizer(config["optimizer_name"], self.model, config["learning_rate"])
        self.scheduler = self._create_scheduler(config["scheduler_name"], self.optimizer)
        self.criterion = self._create_criterion(config["criterion_name"])
        if config["checkpoint"] != "":
            self._load(config["checkpoint"])
        self.curr_epoch = config["curr_epoch"]
        self.name = "{}-{}-{}-{}".format(config["model_name"], config["resolution"], config["batch_size"], config["learning_rate"])
        self.bs = config["batch_size"]
        self.writer = SummaryWriter(log_dir="logs/{}".format(self.name))
        self.writer.flush()
        print("Generated model: {}".format(self.name))
        self.model = nn.DataParallel(self.model).cuda()

        
    def _create_model(self, library, name, pretrained, num_classes):
        if library == "timm":
            return timm.create_model(name, pretrained=pretrained, num_classes=num_classes)
        else:
            return Net(num_classes, 0.1)

    def _create_optimizer(self, name, model_params, lr):
        optim_dict = {"SGD":torch.optim.SGD(model_params.parameters(), lr,weight_decay=2e-5, momentum=0.9, nesterov=True),
                      "SAMSGD": SAMSGD(model_params.parameters(), lr, momentum=0.9,weight_decay=2e-5,nesterov=True)
        }
        return optim_dict[name]
    
    def _create_scheduler(self, name, optimizer):
        scheduler_dict = {
            "StepLR": torch.optim.lr_scheduler.StepLR(optimizer, step_size=2.4, gamma=0.97),
            "CosineAnnealing": torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, 50, 2)
        }
        return scheduler_dict[name]

    def _create_criterion(self, name):
        loss_dict = {"CCE": nn.CrossEntropyLoss().cuda(),
                     "MML": nn.MultiMarginLoss().cuda(),
                     "MSE": nn.MSELoss().cuda(),
                     "BCE": nn.BCELoss().cuda()
                     }
        return loss_dict[name]

    def _load(self, directory):
        print("loading previously trained model...")
        self.model.load_state_dict(torch.load(directory))

    def _save(self, directory, name):
        print("Saving trained {}...".format(name))
        torch.save(self.model.state_dict(), "{}/./{}.pth".format(directory, name))

    def _run_epoch(self, split):
        self.curr_epoch += 1
        self.model.train()
        train_acc, train_loss = self._train_or_eval(split[0], True)
        #self.model.eval()
        with torch.no_grad():
            val_acc, val_loss = self._train_or_eval(split[1], False)
        print(train_acc, train_loss, val_acc, val_loss)
        return train_acc, train_loss, val_acc, val_loss

    #@TODO Add SAMSGD function
    def _train_or_eval(self, loader, train):
        running_loss, correct, total, iterations = 0, 0, 0, 0
        for idx, data in enumerate(loader):
            self.optimizer.zero_grad()
            x, y = data
            preds = self.model(x.cuda())
            loss = self.criterion(preds, y.cuda())
            probs = nn.functional.softmax(preds, 1)
            y_ = torch.argmax(probs, dim=1)
            correct += (y_.cpu()==y.cpu()).sum().item()
            total += y.size(0)
            if train:
                if type(self.optimizer) == SAMSGD:
                    def closure():
                        self.optimizer.zero_grad()
                        outputs = self.model(x.cuda())
                        loss = self.criterion(outputs, y.cuda())
                        loss.backward()
                        return loss
                    self.optimizer.step(closure)
                else:   
                    loss.backward()
                    self.optimizer.step()
                self.scheduler.step()
                print(idx, (correct/total)*100, loss.cpu().item())
            running_loss += loss.cpu().item()
            iterations += 1
            del x, y
            torch.cuda.empty_cache()
        return float(correct/float(total))*100, float(running_loss/iterations)

    def _test(self, loader):
        #self.model.eval()
        with torch.no_grad():
            test_acc, test_loss = self._train_or_eval(loader, False)
        print(test_acc, test_loss)
        return test_acc, test_loss

    def _generate_heatmap_scorecam(self, x, y):
        pass

    #@TODO
    def _add_detector(self):
        pass

    def _update_tensorboard(self):
        pass