# Working with this repository

This is a fork of [ChristophKirst/ClearMap](https://github.com/ChristophKirst/ClearMap),
maintained at <https://github.com/kenjp1223/ClearMap>.

## Use it

```bash
git clone https://github.com/kenjp1223/ClearMap.git
```

Note that the Singularity image already contains a copy of this repository at `/ClearMap`
(cloned at build time). To run a newer checkout, bind-mount it and set `PYTHONPATH` — see the
README.

## Develop on it

```bash
# fork on github, then
git clone https://github.com/<your-username>/ClearMap.git
cd ClearMap

# this fork, so you can pull in its changes
git remote add stuber https://github.com/kenjp1223/ClearMap.git

# the original ClearMap 1, if you need it
git remote add upstream https://github.com/ChristophKirst/ClearMap.git

git fetch --all
```

To pull in changes from this fork:

```bash
git fetch stuber
git merge stuber/master
```

## Contribute back

Commit on a branch, push to your fork, and open a pull request against
`kenjp1223/ClearMap:master`.

```bash
git checkout -b my-change
git add -A
git commit -m "describe what you did"
git push origin my-change
```

Changes to the core ClearMap algorithms (rather than the HPC scripts) are better directed at
[ClearMap2](https://github.com/ChristophKirst/ClearMap2), which is the maintained upstream.

## References

- This fork: <https://github.com/kenjp1223/ClearMap>
- Original ClearMap 1: <https://github.com/ChristophKirst/ClearMap>
- ClearMap2 (current upstream): <https://github.com/ChristophKirst/ClearMap2>
- Git documentation: <https://git-scm.com/doc>
