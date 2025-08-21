# Lab-Protocol

## Before push
run   
```
conda env export > environment.yaml
```   
to export the environment.

## After pull
run  
```
conda env update -f environment.yaml --prune
```
to update the environment.