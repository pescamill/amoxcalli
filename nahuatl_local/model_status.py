"""Disponibilidad del modelo sin cargar sus pesos."""
import importlib.util
from pathlib import Path
from .community import ROOT
DEFAULT_ADAPTER=ROOT/'outputs/continued-unseen/run/best'
def status(adapter=None,enabled=None):
    adapter=Path(adapter or DEFAULT_ADAPTER)
    missing=[m for m in ('torch','transformers','peft') if importlib.util.find_spec(m) is None]
    base=all((ROOT/'models/base'/n).is_file() for n in ('model.safetensors','config.json','tokenizer.json','tokenizer_config.json'))
    trained=all((adapter/n).is_file() for n in ('adapter_config.json','adapter_model.safetensors'))
    return dict(name='Qwen3-0.6B + LoRA',ready=base and trained and not missing and enabled is not False,
                base_ready=base,adapter_ready=trained,missing_dependencies=missing,disabled=enabled is False,
                setup_command='bash scripts/iniciar.sh',note='Generador experimental; requiere revisión lingüística.')
