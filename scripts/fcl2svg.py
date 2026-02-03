import argparse
import os
import sys
import re

def dms_to_decimal(dms_str):
    """
    Converts N005.15.44.694 into decimal degrees.
    Formula: Degrees + (Minutes/60) + (Seconds.Milliseconds/3600)
    """
    if not dms_str:
        return None
    
    direction = dms_str[0].upper()
    # Extract all numeric groups. For N005.15.44.694 -> ['005', '15', '44', '694']
    numbers = re.findall(r'\d+', dms_str)
    
    if len(numbers) < 3:
        return None

    deg = float(numbers[0])
    mins = float(numbers[1])
    
    # Handle seconds and milliseconds (e.g., '44' and '694' -> 44.694)
    if len(numbers) >= 4:
        secs = float(f"{numbers[2]}.{numbers[3]}")
    else:
        secs = float(numbers[2])
    
    decimal = deg + (mins / 60) + (secs / 3600)
    
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

def parse_file(filepath):
    polygons = {}
    current_group = None
    
    # Regex to identify lines starting with N, S, E, W
    coord_pattern = re.compile(r'^[NSEW]\d')

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # If line starts with a coordinate prefix
            if coord_pattern.match(line):
                # Split by semicolon to get Lat and Lon parts
                parts = [p.strip() for p in line.split(';') if p.strip()]
                if len(parts) >= 2 and current_group:
                    lat = dms_to_decimal(parts[0])
                    lon = dms_to_decimal(parts[1])
                    if lat is not None and lon is not None:
                        polygons[current_group].append((lon, lat))
            
            # If line is a header (contains ; but isn't a coordinate)
            elif ';' in line:
                # Get the first part as the ID (e.g., SKQU_TWR)
                current_group = line.split(';')[0].strip()
                polygons[current_group] = []
                
    return {k: v for k, v in polygons.items() if v}

def write_svg(filename, polys, min_x, min_y, scale, view_size):
    # Vibrant colors for airspaces
    colors = ['#845EC2', '#D65DB1', '#FF6F91', '#FF9671', '#FFC75F', '#F9F871', '#008F7A', '#00C9A7', '#0081CF', '#845EC2', '#D65DB1', '#FF6F91', '#FF9671', '#4FFBDF']
    margin = 50
    
    header = (
        f'<svg viewBox="{-margin} {-margin} {view_size + (margin*2)} {view_size + (margin*2)}" '
        f'xmlns="http://www.w3.org/2000/svg" style="background:#121212;">\n'
    )
    
    body = []
    for i, (group_id, points) in enumerate(polys.items()):
        color = colors[i % len(colors)]
        
        # Build polygon points list
        svg_points = []
        for lon, lat in points:
            # Transform to local viewbox coordinates
            x = (lon - min_x) * scale
            y = view_size - ((lat - min_y) * scale) # Invert Y for North=Up
            svg_points.append(f"{x:.2f},{y:.2f}")
        
        pts_str = " ".join(svg_points)
        body.append(f'  <g id="{group_id}">\n')
        body.append(f'    <polygon points="{pts_str}" fill="{color}" fill-opacity="0.1" '
                    f'stroke="{color}" stroke-width="1.5" />\n')
        body.append(f'  </g>\n')
        
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(header + "".join(body) + "</svg>")

def main():
    parser = argparse.ArgumentParser(description="FCL to SVG Converter")
    parser.add_argument("input", help="Input .fcl file")
    parser.add_argument("-o", "--output", default="airspace.svg", help="Output .svg file")
    parser.add_argument("--split", action="store_true", help="One file per polygon")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"File not found: {args.input}")
        return

    polys = parse_file(args.input)
    
    if not polys:
        print("Error: No valid coordinates found. Please check that each coordinate line starts with N/S/E/W and contains a semicolon.")
        return

    # Calculate bounding box for the entire file
    all_pts = [pt for pts in polys.values() for pt in pts]
    lons = [p[0] for p in all_pts]
    lats = [p[1] for p in all_pts]
    
    min_x, max_x = min(lons), max(lons)
    min_y, max_y = min(lats), max(lats)
    
    view_size = 1000
    # Calculate span to keep aspect ratio
    width_span = max_x - min_x
    height_span = max_y - min_y
    max_span = max(width_span, height_span)
    
    scale = view_size / max_span if max_span != 0 else 1

    if args.split:
        out_folder = args.output.replace('.svg', '')
        os.makedirs(out_folder, exist_ok=True)
        for gid, pts in polys.items():
            write_svg(f"{out_folder}/{gid}.svg", {gid: pts}, min_x, min_y, scale, view_size)
        print(f"Created {len(polys)} individual SVGs in {out_folder}/")
    else:
        write_svg(args.output, polys, min_x, min_y, scale, view_size)
        print(f"Successfully generated {args.output} with {len(polys)} polygons.")

if __name__ == "__main__":
    main()