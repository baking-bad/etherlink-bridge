# Bridge [Ticketer]

Prototyping L1 => L2 token bridge

### Build
```
make compile
```

### Run tests
```
poetry install
poetry shell
python -m pytest
```
NOTE that the first time tests run, some time required to pull sandboxed-node

### Lint python code
```
python -m mypy --strict .
```
