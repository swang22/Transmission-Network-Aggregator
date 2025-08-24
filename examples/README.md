# Examples

This folder contains example scripts and their outputs.

## Scripts

### `generate_examples.py`
Creates multiple example visualizations demonstrating different features:
- State-level maps (Texas, California, Florida)
- Zone-level maps (Alabama, Bay Area) 
- Interconnect-level maps (Western, Eastern)
- Both static (PNG) and interactive (HTML) formats

**Usage:**
```bash
cd examples
python generate_examples.py
```

## Sample Outputs

The script generates visualizations in the `outputs/` folder:
- `texas_transmission.png` - Texas state transmission network
- `california_interactive.html` - Interactive California map
- `alabama_zone.png` - Alabama zone visualization
- `western_interconnect.png` - Western Interconnect overview
- `eastern_interactive.html` - Interactive Eastern Interconnect map

## Customization

You can modify `generate_examples.py` to:
- Add new regions or interconnects
- Change figure sizes
- Adjust output formats
- Customize styling options

Each visualization uses capacity classes to distinguish transmission lines:
- **< 200 MW**: Distribution level (thin lines)
- **200-500 MW**: Sub-transmission (light lines)
- **500-1K MW**: Transmission (medium lines)  
- **1K-2K MW**: High voltage (thick lines)
- **2K-5K MW**: Extra high voltage (very thick lines)
- **5K+ MW**: Ultra high voltage corridors (thickest lines)
