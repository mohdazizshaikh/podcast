"""Dedicated local CPU process for dashboard portrait inference."""
import sys
from pathlib import Path
from . import portrait_local,source


def main():
    root,cid,model,seed,steps,result=sys.argv[1:]
    value=portrait_local.generate(Path(root),cid,model=Path(model),seed=int(seed),steps=int(steps),acknowledgment=portrait_local.ACK)
    source.atomic_json(Path(result),value,new=True)


if __name__=="__main__":main()
