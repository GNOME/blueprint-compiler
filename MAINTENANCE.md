## Releasing a new version

1. Look at the git log since the previous release. Note every significant change
in the NEWS file.
2. Update the version number at the top of meson.build according to semver.
3. Make a new commit with just these two changes. Use `Release v{version}`
as the commit message. Tag the commit as `v{version}` and push the tag.
4. Create a "Post-release version bump" commit.
5. Announce the release through relevant channels (Twitter, TWIG, etc.)
