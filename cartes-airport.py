import argparse
import os
import matplotlib
# Forces non-interactive background rendering
matplotlib.use('Agg') 

import matplotlib.pyplot as plt
from cartes.crs import Mercator
from cartes.osm import Overpass
from matplotlib.offsetbox import AnchoredText

def save_airport_map(iata, folder, ext):
    """Downloads and saves a single airport map."""
    print(f"--- Processing {iata} ---")
    
    try:
        # 1. Setup Figure
        fig, ax = plt.subplots(
            figsize=(10, 10), 
            subplot_kw=dict(projection=Mercator())
        )

        # 2. Download Data
        # If this causes a Bus Error, the script may still crash 
        # because Bus Errors are 'hard' signals from the OS.
        airport = Overpass.request(area=dict(iata=iata), aeroway=True)

        # 3. Plotting
        airport.plot(
            ax,
            by="aeroway",
            gate=dict(alpha=0),
            parking_position=dict(alpha=0),
            tower=dict(markersize=500),
            jet_bridge=dict(color="0.3"),
            navigationaid=dict(papi=dict(alpha=0)),
        )
        
        ax.spines["geo"].set_visible(False)
        
        # Add Label
        text = AnchoredText(
            iata, loc=1, frameon=False,
            prop={"size": 30, "fontweight": "bold"}
        )
        ax.add_artist(text)

        # 4. Save
        filename = os.path.join(folder, f"{iata.lower()}.{ext}")
        plt.savefig(filename, dpi=300, bbox_inches='tight', transparent=True)
        plt.close(fig) # Critical to free memory
        print(f"Successfully saved to {filename}")

    except Exception as e:
        print(f"Error processing {iata}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate airport maps from OSM data.")
    
    # --airports BOG CDG AMS
    parser.add_argument("--airports", nargs="+", required=True, help="List of IATA codes")
    
    # --save .
    parser.add_argument("--save", default=".", help="Directory to save the images")
    
    # --format svg
    parser.add_argument("--format", choices=["png", "svg", "pdf"], default="png", help="Output format")

    args = parser.parse_args()

    # Create directory if it doesn't exist
    if not os.path.exists(args.save):
        os.makedirs(args.save)

    for code in args.airports:
        save_airport_map(code.upper(), args.save, args.format)