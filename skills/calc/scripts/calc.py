#!/usr/bin/env python3
"""Calculator and unit converter.
Usage:
  calc.py "expression"        - Evaluate math (Python syntax)
  calc.py convert VAL FROM TO - Unit conversion

Examples:
  calc.py "2**10"
  calc.py "import math; math.sqrt(144)"
  calc.py convert 100 F C
  calc.py convert 25.4 mm in
  calc.py convert 14.7 psi bar
  calc.py convert 100 mph kph
"""
import sys, math

CONVERSIONS = {
    ("F","C"): lambda v: (v-32)*5/9,
    ("C","F"): lambda v: v*9/5+32,
    ("mm","in"): lambda v: v/25.4,
    ("in","mm"): lambda v: v*25.4,
    ("m","ft"): lambda v: v*3.28084,
    ("ft","m"): lambda v: v/3.28084,
    ("kg","lb"): lambda v: v*2.20462,
    ("lb","kg"): lambda v: v/2.20462,
    ("psi","bar"): lambda v: v*0.0689476,
    ("bar","psi"): lambda v: v/0.0689476,
    ("psi","kpa"): lambda v: v*6.89476,
    ("kpa","psi"): lambda v: v/6.89476,
    ("mph","kph"): lambda v: v*1.60934,
    ("kph","mph"): lambda v: v/1.60934,
    ("L","gal"): lambda v: v*0.264172,
    ("gal","L"): lambda v: v/0.264172,
    ("nm","ftlb"): lambda v: v*0.737562,
    ("ftlb","nm"): lambda v: v/0.737562,
    ("W","hp"): lambda v: v/745.7,
    ("hp","W"): lambda v: v*745.7,
}

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "convert":
        if len(sys.argv) < 5:
            print("Usage: calc.py convert VALUE FROM TO")
            sys.exit(1)
        val = float(sys.argv[2])
        fr = sys.argv[3]
        to = sys.argv[4]
        key = (fr, to)
        if key in CONVERSIONS:
            result = CONVERSIONS[key](val)
            print(f"{val} {fr} = {result:.4f} {to}")
        else:
            print(f"Unknown conversion: {fr} -> {to}")
            print("Available:", ", ".join(f"{a}->{b}" for a,b in CONVERSIONS.keys()))
    else:
        expr = " ".join(sys.argv[1:])
        try:
            result = eval(expr, {"__builtins__": __builtins__, "math": math})
            print(result)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()