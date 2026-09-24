# Optional GitHub Actions workflow

`validate.yml` is an inactive template. It runs structure checks, cleanup tests,
fresh atopile builds, PCB validation and bounded SPICE cases, retaining reports
for seven days. Both referenced GitHub actions are pinned by commit.

The current GitHub OAuth login lacks the `workflow` scope, so GitHub refused an
attempt to install this file under `.github/workflows/`. The project and local
validation do not require changing those permissions.

To enable CI later, use credentials authorized to manage workflows and copy this
file to `.github/workflows/validate.yml`, then commit and push. Local equivalents:

```powershell
python environment/check_project.py
.\lab.ps1 build
.\lab.ps1 unit
.\lab.ps1 test
```
