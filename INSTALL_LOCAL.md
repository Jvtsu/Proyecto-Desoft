# PulsarLab local installation

This version adds a terminal command for the local development workflow.

## 1. Create or activate the environment

```powershell
conda create -n pulsarlab python=3.11 -y
conda activate pulsarlab
```

Or use your existing environment:

```powershell
conda activate pulsarlab
```

## 2. Install PulsarLab locally

From the project root, where `pyproject.toml` is located:

```powershell
pip install -e .
```

This creates the terminal command:

```powershell
plab
```

## 3. Launch PulsarLab with one dataset

```powershell
plab glitAD.par allVF.dat
```

PulsarLab will open the Streamlit interface and preload the `.par` and `.dat`
files automatically.

## 4. Optional arguments

Use a different port:

```powershell
plab glitAD.par allVF.dat --port 8502
```

Run without automatically opening the browser:

```powershell
plab glitAD.par allVF.dat --no-browser
```

Set a dataset name:

```powershell
plab glitAD.par allVF.dat --name "Glitch AD"
```

Validate the command without launching:

```powershell
plab glitAD.par allVF.dat --dry-run
```

## 5. Check installation

```powershell
plab --help
plab --version
```

## 6. Remove local installation

```powershell
pip uninstall pulsarlab
```

## Notes

The CLI does not replace the Streamlit interface. It only makes the launch
workflow cleaner:

```text
.par + .dat -> plab command -> PulsarLab interface
```
