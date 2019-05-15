# Manifestgen

## Company Internal

A tool to generate a loftsman manifest from a blob.

## Install

This is built as an RPM and can be installed via yum/zypper. You can also install via:

    pip install .

## Usage

```
manifestgen --charts-path /path/to/blob/helm -o manifest.yaml
cat manifest.yaml
```
OR
```
manifestgen --charts-repo http://helmrepo.dev.cray.com:8080 -o manifest.yaml
cat manifest.yaml
```
