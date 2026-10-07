from pathlib import Path
import zipfile
import os
import tempfile
root=Path(__file__).resolve().parents[1]
handle,temporary=tempfile.mkstemp(prefix='nahuatl-package-',suffix='.zip',dir=root.parent)
os.close(handle)
with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if not path.is_file() or any(p in rel.parts for p in ['__pycache__','.venv','.git','node_modules','.pytest_cache']):continue
        if rel.parts[0]=='models':continue
        # Solo la referencia bilingüe auditable; nunca perfiles, propuestas,
        # audios, respaldos privados o páginas descargadas de los catálogos.
        if rel.parts[0]=='data' and rel.parts[:2]!=('data','training-reference'):continue
        if rel.parts[0]=='outputs' and (len(rel.parts)<2 or rel.parts[1] not in ['classical-v2','automatic','continued-unseen']):continue
        if any(part.endswith(('-writing','-previous')) for part in rel.parts) or path.suffix in ['.tmp','.lock','.sqlite3','.sqlite3-wal','.sqlite3-shm','.db','.db-wal','.db-shm']:continue
        if path.name.endswith('-full.json') or (path.suffix=='.log' and path.name not in ['train.log','autotrain-run.log']) or path.name in ['pilot-summary.json','offline-v1-probe.json','offline-check.json','tests.txt']:continue
        archive.write(path,Path('nahuatl-local')/rel)
os.replace(temporary,root.parent/'nahuatl-local.zip')
print(root.parent/'nahuatl-local.zip')
