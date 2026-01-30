#!/usr/bin/env python3
"""
Well Depth Lookup Tool for Southern California Well Service
Queries CA DWR Well Completion Reports by address or coordinates.

Usage:
    welldepth "123 Main St, Ramona, CA"
    welldepth --lat 33.05 --lon -116.87
    welldepth --apn "123-456-78"
"""

import argparse
import json
import math
import sys
from statistics import mean, median
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from collections import Counter

# Google Maps API key (from Clawdbot config)
GOOGLE_API_KEY = "AIzaSyBdW_b5GyhrKG6_ov-6QarU62bkW8k1Mbo"

# CA DWR Well Completion Reports API
DWR_API_BASE = "https://gis.water.ca.gov/arcgis/rest/services/Environment/i07_WellCompletionReports/FeatureServer/0/query"

# Default search radius in miles
DEFAULT_RADIUS_MILES = 1.0

# Fields to retrieve from DWR
FIELDS = [
    "TotalDrillDepth",
    "TotalCompletedDepth",
    "DrillingMethod",
    "Fluid",  # Air vs Bentonite (mud) vs Water
    "CasingDiameter",
    "WellYield",
    "WellYieldUnitofMeasure",
    "DecimalLatitude",
    "DecimalLongitude",
    "APN",
    "PlannedUseFormerUse",
    "RecordType",
    "DateWorkEnded",
    "WCRNumber",
    "WCRLinks",
    "CountyName",
    "City",
    "WellLocation"
]

def get_drilling_type(method: str, fluid: str) -> str:
    """Combine drilling method and fluid to get specific drilling type."""
    method = method or "Unknown"
    fluid = fluid or ""
    
    # Normalize
    method_lower = method.lower()
    fluid_lower = fluid.lower()
    
    # Handle "Other" method with specific fluid - common in DWR data
    if method_lower == "other":
        if fluid_lower == "air":
            return "Air Rotary"
        elif fluid_lower in ("bentonite", "foam", "polymer", "drilling mud"):
            return "Mud Rotary"
        elif fluid_lower == "water":
            return "Mud Rotary"  # Water drilling is typically mud rotary
        elif fluid_lower == "none":
            return "Unknown"
        else:
            return "Unknown"
    
    # Determine if air or mud rotary
    if "rotary" in method_lower or "direct" in method_lower:
        if fluid_lower == "air":
            return "Air Rotary"
        elif fluid_lower in ("bentonite", "foam", "polymer", "drilling mud", "water"):
            return "Mud Rotary"
        elif fluid_lower == "none":
            return "Rotary (Unknown)"
        else:
            return "Rotary (Unknown)"
    elif "cable" in method_lower:
        return "Cable Tool"
    elif "auger" in method_lower:
        return "Auger"
    elif "hammer" in method_lower:
        if fluid_lower == "air":
            return "Air Hammer"
        else:
            return "Downhole Hammer"
    elif "reverse" in method_lower:
        if fluid_lower == "air":
            return "Reverse Circulation (Air)"
        else:
            return "Reverse Circulation (Mud)"
    else:
        return method if method not in ("Unknown", "") else "Unknown"


from typing import Optional, Tuple, List, Dict

def geocode_address(address: str) -> Tuple[float, float, str]:
    """Convert address to lat/lon using Nominatim (OpenStreetMap) API."""
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "us"
    }
    url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
    
    try:
        req = Request(url, headers={"User-Agent": "WellDepthTool/1.0 (SCWS)"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        raise RuntimeError(f"Geocoding failed: {e}")
    
    if not data:
        raise RuntimeError(f"Could not geocode address: No results found")
    
    result = data[0]
    lat = float(result["lat"])
    lon = float(result["lon"])
    formatted = result.get("display_name", address)
    
    return lat, lon, formatted


def miles_to_meters(miles: float) -> float:
    """Convert miles to meters."""
    return miles * 1609.344


def query_wells(lat: float, lon: float, radius_miles: float = DEFAULT_RADIUS_MILES, 
                county: str = None, max_results: int = 500) -> List[Dict]:
    """Query DWR API for wells within radius of coordinates."""
    
    # Calculate bounding box from center point and radius
    # Approximate: 1 degree lat = 69 miles, 1 degree lon = 69 * cos(lat) miles
    lat_offset = radius_miles / 69.0
    lon_offset = radius_miles / (69.0 * math.cos(math.radians(lat)))
    
    min_lat = lat - lat_offset
    max_lat = lat + lat_offset
    min_lon = lon - lon_offset
    max_lon = lon + lon_offset
    
    # Use envelope (bounding box) geometry
    geometry = json.dumps({
        "xmin": min_lon,
        "ymin": min_lat,
        "xmax": max_lon,
        "ymax": max_lat,
        "spatialReference": {"wkid": 4326}
    })
    
    where_clause = "1=1"
    if county:
        where_clause = f"CountyName='{county}'"
    
    params = {
        "where": where_clause,
        "geometry": geometry,
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 4326,
        "outFields": ",".join(FIELDS),
        "returnGeometry": "false",
        "resultRecordCount": max_results,
        "f": "json"
    }
    
    url = f"{DWR_API_BASE}?{urlencode(params)}"
    
    try:
        req = Request(url, headers={"User-Agent": "WellDepthTool/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        raise RuntimeError(f"DWR API query failed: {e}")
    
    if "error" in data:
        raise RuntimeError(f"DWR API error: {data['error'].get('message', 'Unknown')}")
    
    features = data.get("features", [])
    return [f["attributes"] for f in features]


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles (Haversine formula)."""
    R = 3959  # Earth radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def parse_depth(value) -> Optional[float]:
    """Parse depth value to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        # Handle string values like "350" or "350.00"
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def analyze_wells(wells: List[Dict], center_lat: float, center_lon: float) -> Dict:
    """Analyze well data and return statistics."""
    
    if not wells:
        return {"count": 0, "message": "No wells found in this area"}
    
    # Parse depths
    depths = []
    completed_depths = []
    yields = []
    drilling_methods = []
    casing_sizes = []
    uses = []
    record_types = []
    
    wells_with_distance = []
    
    for w in wells:
        # Calculate distance from center
        wlat = w.get("DecimalLatitude")
        wlon = w.get("DecimalLongitude")
        if wlat and wlon:
            dist = calculate_distance(center_lat, center_lon, wlat, wlon)
            w["_distance_miles"] = dist
            wells_with_distance.append(w)
        
        # Parse drill depth
        depth = parse_depth(w.get("TotalDrillDepth"))
        if depth and depth > 0 and depth < 5000:  # Sanity check
            depths.append(depth)
        
        # Parse completed depth
        comp_depth = parse_depth(w.get("TotalCompletedDepth"))
        if comp_depth and comp_depth > 0 and comp_depth < 5000:
            completed_depths.append(comp_depth)
        
        # Parse yield
        well_yield = parse_depth(w.get("WellYield"))
        if well_yield and well_yield > 0:
            yields.append(well_yield)
        
        # Collect categorical data - combine method + fluid for drilling type
        method = w.get("DrillingMethod")
        fluid = w.get("Fluid")
        drilling_type = get_drilling_type(method, fluid)
        if drilling_type and drilling_type not in ("Unknown",):
            drilling_methods.append(drilling_type)
        
        casing = w.get("CasingDiameter")
        if casing and casing not in (None, ""):
            casing_sizes.append(str(casing))
        
        use = w.get("PlannedUseFormerUse")
        if use and use not in (None, "", "Unknown"):
            uses.append(use)
        
        rtype = w.get("RecordType")
        if rtype:
            record_types.append(rtype)
    
    # Sort by distance
    wells_with_distance.sort(key=lambda x: x.get("_distance_miles", 999))
    
    # Build result
    wells_with_any_depth = len([1 for d in depths if d] + [1 for d in completed_depths if d])
    result = {
        "count": len(wells),
        "wells_with_depth_data": max(len(depths), len(completed_depths)),
    }
    
    # Depth statistics
    if depths:
        result["depth"] = {
            "min": min(depths),
            "max": max(depths),
            "mean": round(mean(depths), 1),
            "median": round(median(depths), 1),
            "samples": len(depths)
        }
    
    if completed_depths:
        result["completed_depth"] = {
            "min": min(completed_depths),
            "max": max(completed_depths),
            "mean": round(mean(completed_depths), 1),
            "median": round(median(completed_depths), 1),
            "samples": len(completed_depths)
        }
    
    # Yield statistics
    if yields:
        result["yield_gpm"] = {
            "min": min(yields),
            "max": max(yields),
            "mean": round(mean(yields), 1),
            "median": round(median(yields), 1),
            "samples": len(yields)
        }
    
    # Most common drilling methods
    if drilling_methods:
        method_counts = Counter(drilling_methods).most_common(5)
        result["drilling_methods"] = [{"method": m, "count": c} for m, c in method_counts]
    
    # Most common casing sizes
    if casing_sizes:
        casing_counts = Counter(casing_sizes).most_common(5)
        result["casing_sizes"] = [{"size": s, "count": c} for s, c in casing_counts]
    
    # Most common uses
    if uses:
        use_counts = Counter(uses).most_common(5)
        result["planned_uses"] = [{"use": u, "count": c} for u, c in use_counts]
    
    # Record types (New vs Destruction vs Modification)
    if record_types:
        type_counts = Counter(record_types).most_common()
        result["record_types"] = [{"type": t, "count": c} for t, c in type_counts]
    
    # Nearest wells with details (prioritize ones with depth data)
    wells_with_depth = [w for w in wells_with_distance if parse_depth(w.get("TotalDrillDepth")) or parse_depth(w.get("TotalCompletedDepth"))]
    wells_no_depth = [w for w in wells_with_distance if not (parse_depth(w.get("TotalDrillDepth")) or parse_depth(w.get("TotalCompletedDepth")))]
    prioritized_wells = wells_with_depth[:10] if len(wells_with_depth) >= 10 else wells_with_depth + wells_no_depth[:10-len(wells_with_depth)]
    
    nearest = []
    for w in prioritized_wells[:10]:
        drill_depth = parse_depth(w.get("TotalDrillDepth"))
        completed_depth = parse_depth(w.get("TotalCompletedDepth"))
        # Use drill depth if available, otherwise completed depth
        best_depth = drill_depth or completed_depth
        
        drilling_type = get_drilling_type(w.get("DrillingMethod"), w.get("Fluid"))
        
        well_info = {
            "distance_miles": round(w.get("_distance_miles", 0), 2),
            "depth": best_depth,
            "drill_depth": drill_depth,
            "completed_depth": completed_depth,
            "method": drilling_type,
            "fluid": w.get("Fluid"),
            "yield_gpm": parse_depth(w.get("WellYield")),
            "casing": w.get("CasingDiameter"),
            "use": w.get("PlannedUseFormerUse"),
            "type": w.get("RecordType"),
            "wcr": w.get("WCRNumber"),
            "pdf": w.get("WCRLinks"),
            "address": w.get("WellLocation"),
            "city": w.get("City"),
            "apn": w.get("APN")
        }
        # Filter out None values for cleaner output
        well_info = {k: v for k, v in well_info.items() if v is not None}
        nearest.append(well_info)
    
    result["nearest_wells"] = nearest
    
    return result


def format_output(location: str, lat: float, lon: float, radius: float, analysis: dict) -> str:
    """Format analysis results for display."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"WELL DEPTH LOOKUP - Southern California Well Service")
    lines.append("=" * 60)
    lines.append(f"📍 Location: {location}")
    lines.append(f"   Coordinates: {lat:.6f}, {lon:.6f}")
    lines.append(f"   Search radius: {radius} miles")
    lines.append("")
    
    if analysis.get("count", 0) == 0:
        lines.append("❌ No wells found in this area.")
        lines.append("   Try increasing the search radius with --radius")
        return "\n".join(lines)
    
    lines.append(f"📊 SUMMARY ({analysis['count']} wells found, {analysis.get('wells_with_depth_data', 0)} with depth data)")
    lines.append("-" * 60)
    
    # Depth stats - show completed depth first (more commonly filled), then drill depth
    if "completed_depth" in analysis:
        d = analysis["completed_depth"]
        lines.append(f"")
        lines.append(f"⛏️  WELL DEPTH (n={d['samples']})")
        lines.append(f"    Range: {d['min']:.0f} - {d['max']:.0f} ft")
        lines.append(f"    Average: {d['mean']:.0f} ft")
        lines.append(f"    Median: {d['median']:.0f} ft  ← typical for this area")
    elif "depth" in analysis:
        d = analysis["depth"]
        lines.append(f"")
        lines.append(f"⛏️  WELL DEPTH (n={d['samples']})")
        lines.append(f"    Range: {d['min']:.0f} - {d['max']:.0f} ft")
        lines.append(f"    Average: {d['mean']:.0f} ft")
        lines.append(f"    Median: {d['median']:.0f} ft  ← typical for this area")
    
    # Yield stats
    if "yield_gpm" in analysis:
        y = analysis["yield_gpm"]
        lines.append(f"")
        lines.append(f"💧 WELL YIELD (n={y['samples']})")
        lines.append(f"    Range: {y['min']:.0f} - {y['max']:.0f} GPM")
        lines.append(f"    Average: {y['mean']:.0f} GPM")
        lines.append(f"    Median: {y['median']:.0f} GPM")
    
    # Drilling methods
    if "drilling_methods" in analysis:
        lines.append(f"")
        lines.append(f"🔧 DRILLING METHODS")
        for m in analysis["drilling_methods"]:
            lines.append(f"    • {m['method']}: {m['count']}")
    
    # Casing sizes
    if "casing_sizes" in analysis:
        lines.append(f"")
        lines.append(f"🔩 CASING SIZES")
        for c in analysis["casing_sizes"]:
            lines.append(f"    • {c['size']}\": {c['count']}")
    
    # Nearest wells
    if "nearest_wells" in analysis and analysis["nearest_wells"]:
        lines.append(f"")
        lines.append(f"📍 NEAREST WELLS")
        lines.append("-" * 60)
        for i, w in enumerate(analysis["nearest_wells"][:5], 1):
            dist = w.get('distance_miles', '?')
            depth = w.get('depth', '?')
            method = w.get('method', 'Unknown')
            yield_gpm = w.get('yield_gpm', '?')
            use = w.get('use', '')
            wcr = w.get('wcr', '')
            
            lines.append(f"")
            lines.append(f"  {i}. {dist} mi away - {depth} ft deep")
            lines.append(f"     Method: {method} | Yield: {yield_gpm} GPM")
            if use:
                lines.append(f"     Use: {use}")
            if w.get('address'):
                lines.append(f"     Address: {w.get('address')}")
            if w.get('pdf'):
                lines.append(f"     PDF: {w.get('pdf')}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Look up well depth data from CA DWR Well Completion Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  welldepth "123 Main St, Ramona, CA"
  welldepth "Ramona, CA" --radius 5
  welldepth --lat 33.05 --lon -116.87
  welldepth --lat 33.05 --lon -116.87 --json
        """
    )
    
    parser.add_argument("address", nargs="?", help="Address to look up")
    parser.add_argument("--lat", type=float, help="Latitude (decimal degrees)")
    parser.add_argument("--lon", type=float, help="Longitude (decimal degrees)")
    parser.add_argument("--radius", type=float, default=DEFAULT_RADIUS_MILES,
                        help=f"Search radius in miles (default: {DEFAULT_RADIUS_MILES})")
    parser.add_argument("--county", help="Filter by county name")
    parser.add_argument("--max", type=int, default=500, help="Maximum wells to retrieve")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--raw", action="store_true", help="Output raw well data as JSON")
    
    args = parser.parse_args()
    
    # Determine location
    if args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
        location = f"{lat}, {lon}"
    elif args.address:
        try:
            lat, lon, location = geocode_address(args.address)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Query wells
    try:
        wells = query_wells(lat, lon, args.radius, args.county, args.max)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output raw data if requested
    if args.raw:
        print(json.dumps(wells, indent=2))
        sys.exit(0)
    
    # Analyze
    analysis = analyze_wells(wells, lat, lon)
    analysis["location"] = location
    analysis["coordinates"] = {"lat": lat, "lon": lon}
    analysis["radius_miles"] = args.radius
    
    # Output
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(format_output(location, lat, lon, args.radius, analysis))


if __name__ == "__main__":
    main()
