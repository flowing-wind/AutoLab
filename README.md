# Lab-Protocol

## Before push
run   
```bash
conda env export > environment.yaml
```   
to export the environment.

## After pull
run  
```bash
conda env update -f environment.yaml --prune
```
to update the environment.