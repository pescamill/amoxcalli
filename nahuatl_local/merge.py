import argparse
from pathlib import Path
from .runtime import load_model
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('adapter');p.add_argument('output');a=p.parse_args()
    if Path(a.output).exists():raise SystemExit('El destino ya existe.')
    model,tok,_=load_model(ROOT/'models/base',a.adapter,'cpu')
    model.merge_and_unload().save_pretrained(a.output,safe_serialization=True);tok.save_pretrained(a.output)
if __name__=='__main__':main()
