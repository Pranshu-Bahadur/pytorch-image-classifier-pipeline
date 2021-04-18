import torch
import argparse
from experiment import Experiment


def _model_config(args):
    config = {
        "model_name": args.model,
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "optimizer_name": args.optimizer,
        "criterion_name": args.loss,
        "scheduler_name": args.scheduler,
        "checkpoint": args.checkpoint if args.checkpoint else "",
        "num_classes": int(args.num_classes),
        "curr_epoch": int(args.curr_epoch) if args.curr_epoch else 0,
        "resolution": int(args.resolution),
        "epochs": int(args.epochs) if args.epochs else 0,
        "train": True if args.train else False,
        "library": args.library,
        "save_directory": args.save_directory
    }
    return config

if __name__ == "main":
    torch.backends.cudnn.enabled = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", "-m", help="Pick a model name")
    parser.add_argument("--dataset_directory", "-d", help="Set dataset directory path")
    parser.add_argument("--resolution", "-r", help="Set image resolution")
    parser.add_argument("--batch_size", "-b", help="Set batch size")
    parser.add_argument("--learning_rate", "-l", help="set initial learning rate")
    parser.add_argument("--checkpoint", "-c", help="Specify path for model to be loaded")
    parser.add_argument("--num_classes", "-n", help="set num classes")
    parser.add_argument("--curr_epoch", "-e", help="Set number of epochs already trained")
    parser.add_argument("--epochs", "-f", help="Train for these many more epochs")
    parser.add_argument("--optimizer", help="Choose an optimizer")
    parser.add_argument("--scheduler", help="Choose a scheduler")
    parser.add_argument("--loss", help="Choose a loss criterion")
    parser.add_argument("--train", help="Set this model to train mode", action="store_true")
    parser.add_argument("--library")
    parser.add_argument("--save_directory", "-s")
    args = parser.parse_args()
    config = _model_config(args)
    experiment = Experiment(config)
    if args.train:
        experiment._run(args.dataset_directory, config)

