import matplotlib
# Use 'Agg' to avoid GUI issues, or 'MacOSX' if you want a popup window
matplotlib.use('Agg') 

import matplotlib.pyplot as plt
from cartes.crs import Mercator
from cartes.osm import Overpass
from matplotlib.offsetbox import AnchoredText

# 1. Define the grid and projection
fig, ax = plt.subplots(
    3, 3, figsize=(15, 15),
    subplot_kw=dict(projection=Mercator())
)

# 2. Fill the 3x3 grid (9 airports)
# The values (1-4) represent the corner for the label
locs = {
    "AMS": 1, "BOG": 4, "SFO": 1,
    "DXB": 2, "SIN": 3, "CDG": 1,
    "HND": 2, "ATL": 4, "LHR": 3
}

# 3. Iterate and Plot
for ax_, (iata, label_loc) in zip(ax.ravel(), locs.items()):
    print(f"Processing {iata}...")
    
    try:
        # Download data (or get from cache)
        airport = Overpass.request(area=dict(iata=iata), aeroway=True)

        airport.plot(
            ax_,
            by="aeroway",
            # Style overrides
            gate=dict(alpha=0),  # mute
            parking_position=dict(alpha=0),  # mute
            tower=dict(markersize=500),  # scale down
            jet_bridge=dict(color="0.3"),  # dark grey
            navigationaid=dict(papi=dict(alpha=0)),  # mute
        )
        
        # Clean up the map aesthetic
        ax_.spines["geo"].set_visible(False)

        # Add the IATA label
        # Note: 'Fira Sans' must be installed on your system or it defaults
        text = AnchoredText(
            iata, loc=label_loc, frameon=False,
            prop={"size": 24, "fontweight": "bold"},
        )
        ax_.add_artist(text)
        
    except Exception as e:
        print(f"Could not plot {iata}: {e}")

# 4. Save the output
plt.tight_layout()
fig.savefig("airport_grid.png", dpi=300, bbox_inches='tight')
print("\nSuccess! Map saved as 'airport_grid.png'")