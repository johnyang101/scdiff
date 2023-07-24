from omegaconf import DictConfig
import hydra
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.callbacks import ModelCheckpoint
from cellot.models.cond_score_module import CondScoreModule
from cellot.data.sciplex_ae_dm import CellDataModule
from cellot.train.utils import get_free_gpu
import os

@hydra.main(config_path="../../configs/diff", config_name="base.yaml")
def main(cfg: DictConfig) -> None:
    # Prepare data
    data_module = CellDataModule(cfg)
    
    # Train model
    train_model(cfg, data_module)

def train_model(cfg: DictConfig, data_module: CellDataModule):
    # Load or initialize the model
    if cfg.WARM_START:
        model = CondScoreModule.load_from_checkpoint(checkpoint_path=cfg.WARM_START_PATH, hparams=cfg)
        cfg.experiment.wandb_logger.name = cfg.experiment.wandb_logger.name + '_WS'
    else:
        model = CondScoreModule(cfg)

    # Define device strategy
    if cfg.trainer.strategy == 'auto':
        replica_id = int(get_free_gpu())
        trainer_devices = [replica_id]
    else: 
        trainer_devices = cfg.DEVICES
    
    # Set debug mode if required
    if cfg.DEBUG:
        os.environ["WANDB_MODE"] = "dryrun"

    # Initialize logger
    logger = WandbLogger(**cfg.experiment.wandb_logger)

    # Initialize and run the trainer
    trainer = Trainer(logger=logger, devices=trainer_devices, **cfg.trainer)
    trainer.fit(model, datamodule=data_module)

if __name__ == "__main__":
    main()