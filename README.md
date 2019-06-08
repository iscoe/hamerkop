# Hamerkop

The hamerkop is a wading bird found in much of Africa including Ethiopia.
As a wading bird, it spends a lot of time standing in muck and 
sticking its open bill into mud hoping to catch something to eat.
It has also been observed feeding off the backs of hippopotamuses.

Hamerkop is also a python framework for building entity linking systems.
It supports the creation of pipelines for in document coreference,
candidate generation, and entity resolution.
Hamerkop defines the API for these stages and provides some default
implementations.
Hamerkop was developed for LoReHLT (Low Resource HLT) evaluations.
Prounciation is hammer-cop. 

## License and Copyright

Copyright 2017-2019 Johns Hopkins University Applied Physics Laboratory

Licensed under the Apache License, Version 2.0

## Installing

Hamerkop requires python 3.

```bash
pip install hamerkop
```

## Using

```python
import hamerkop
import os
import sys

ifn = sys.argv[1]
ofn = sys.argv[2]

# load kb
kb_dir = sys.argv[3]
entities_fn = os.path.join(kb_dir, 'entities.tab')
names_fn = os.path.join(kb_dir, 'alternate_names.tab')
with open(entities_fn, 'r') as efp, open(names_fn, 'r') as nfp:
    kb = hamerkop.MemoryKB(efp, nfp)
    index = hamerkop.ExactMatchMemoryNameIndex(kb)

# construct pipeline components
pre = hamerkop.PassThru()
coref = hamerkop.ExactMatchCoRef()
cand = hamerkop.IndexBasedGenerator(10, index)
resolver = hamerkop.BestMatchResolver()

with open(ifn, 'r') as ifp, open(ofn, 'w') as ofp:
    reader = hamerkop.InputReader(ifp)
    writer = hamerkop.OutputWriter(ofp, 'my EL system')
    pipeline = hamerkop.Pipeline(reader, pre, coref, cand, resolver, writer)
    pipeline.run()
```

## Development
After creating a virtual environment, install hamerkop's dependencies:

```bash
pip install -r requirements.txt
```

To run the tests, install nose with pip and then:

```bash
nosetests
```

To check compliance with a lightly modified PEP8 coding standard,
install flake8 with pip and then run:

```bash
flake8 hamerkop
```
