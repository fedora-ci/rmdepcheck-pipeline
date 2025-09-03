# rmdepcheck

This repository contains the Fedora-CI test for [rmdepcheck].

[rmdepcheck]: https://codeberg.org/AdamWill/rmdepcheck

## Manual execution

To run this test manually simply run the tmt plan providing the following inputs:
- `distro` \[context\]: Base distro to run against
- `KOJI_TASK_ID` \[environment\]: Koji task id to test

For example:
```console
$ tmt -c distro=fedora-rawhide run -a \
  -e KOJI_TASK_ID=43617203 \
  provision --how container
```
