import json
import os

from transformers import AutoConfig as HfAutoConfig
from transformers.configuration_utils import CONFIG_NAME as HF_CONFIG_NAME

from ...constants import MCA_CONFIG_NAME
from ...utils import get_logger
from ..model_config import McaModelConfig
from ..qwen2_5_vl import Qwen2_5_VLConfig
from ..qwen2_vl import Qwen2VLConfig


logger = get_logger(__name__)


CONFIG_MAPPING_NAMES = {
    "llama": McaModelConfig,
    "qwen2": McaModelConfig,
    "qwen3": McaModelConfig,
    "qwen2_moe": McaModelConfig,
    "qwen3_moe": McaModelConfig,
    "qwen2_vl": Qwen2VLConfig,
    "qwen2_5_vl": Qwen2_5_VLConfig,
    "glm4_moe": McaModelConfig,
}


def get_config_cls(model_type) -> McaModelConfig:
    cls = CONFIG_MAPPING_NAMES.get(model_type, None)
    if cls is None:
        logger.warning(f"No config found for model type {model_type}, use McaModelConfig!")
        cls = McaModelConfig
    return cls

def register_config(model_type, config_cls):
    cls = CONFIG_MAPPING_NAMES.get(model_type, None)
    if cls is not None:
        logger.warning(f"Config for model type {model_type} already registered, set {cls} to {config_cls}!")
    CONFIG_MAPPING_NAMES[model_type] = config_cls

class AutoConfig:
    @classmethod
    def for_model(cls, model_type: str, *args, **kwargs) -> McaModelConfig:
        config_class = get_config_cls(model_type)
        return config_class(*args, **kwargs)

    @classmethod
    def from_pretrained(cls, model_name_or_path, *args, **kwargs) -> McaModelConfig:
        config_file = os.path.join(model_name_or_path, MCA_CONFIG_NAME)
        model_type = None
        if os.path.isfile(config_file):
            with open(config_file, "r", encoding="utf-8") as reader:
                text = reader.read()
            config_values = json.loads(text)
            model_type = config_values.get("hf_model_type")
        elif os.path.isfile(os.path.join(model_name_or_path, HF_CONFIG_NAME)):
            # from hf ckpt
            logger.info(f"Did not find {config_file}, loading HuggingFace config from {model_name_or_path}")
            hf_config = HfAutoConfig.from_pretrained(model_name_or_path, trust_remote_code=True)
            model_type = hf_config.model_type

        if model_type is None:
            raise ValueError(f"No valid config found in {model_name_or_path}")
        config_class = get_config_cls(model_type)
        return config_class.from_pretrained(model_name_or_path, *args, **kwargs)
