"""
rainin_preprocess.py
--------------------
Converts NIWA TMY3 EPW + STAT files into the compact JSON data file
embedded in rainin.html.

Run this if you have updated EPW/STAT files from NIWA and need to
regenerate rainin_data.json.

Usage:
    python rainin_preprocess.py --epw ./epw --stat ./stat --out rainin_data.json

Expects files named TMY3_NZ_XX.epw and TMY3_NZ_XX.stat where XX is the
two-letter station code.

Requirements: Python 3.8+, no external dependencies.

Licence: MIT
"""

import json
import gzip
import os
import re
import argparse
from collections import defaultdict

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def parse_epw(path):
    """Parse a single EPW file. Returns (meta dict, daily arrays)."""
    rows = []
    meta = {}
    with open(path, 'r', errors='replace') as f:
        for i, line in enumerate(f):
            if i == 0:
                parts = line.strip().split(',')
                meta = {
                    'city':   parts[1].strip(),
                    'region': parts[2].strip(),
                    'lat':    float(parts[6]),
                    'lon':    float(parts[7]),
                }
            if i < 8:
                continue
            fields = line.strip().split(',')
            if len(fields) < 34:
                continue
            rows.append(fields)

    # Aggregate hourly → daily
    daily = defaultdict(lambda: {
        'temps': [], 'rh_wh': [], 'wind': [], 'precip': 0.0
    })
    for r in rows:
        m, d, hr = int(r[1]), int(r[2]), int(r[3])
        key = (m, d)
        try:
            daily[key]['temps'].append(float(r[6]))
            if 7 <= hr <= 17:               # work-hours RH only
                rh = float(r[8])
                if rh < 999:
                    daily[key]['rh_wh'].append(rh)
            daily[key]['wind'].append(float(r[21]))
            p = float(r[33])
            if p < 900:
                daily[key]['precip'] += p
        except (ValueError, IndexError):
            pass

    # Build ordered 365-day arrays
    rain, wind, temp, rh = [], [], [], []
    for mo in range(1, 13):
        for dy in range(1, DAYS_IN_MONTH[mo - 1] + 1):
            v = daily.get((mo, dy), {
                'temps': [15.0], 'rh_wh': [70.0],
                'wind': [5.0], 'precip': 0.0
            })
            rain.append(round(v['precip'], 1))
            wind.append(round(max(v['wind']) * 3.6, 1) if v['wind'] else 0.0)
            temp.append(round(min(v['temps']), 1) if v['temps'] else 5.0)
            rh.append(round(max(v['rh_wh']), 0) if v['rh_wh'] else 70.0)

    return meta, rain, wind, temp, rh


def parse_stat(path):
    """Parse a STAT file for supplementary monthly/scalar data."""
    with open(path, 'r', encoding='iso-8859-1', errors='replace') as f:
        txt = f.read()

    out = {}

    # Monthly average temp and wind
    m = re.search(
        r'Monthly Statistics for Dry Bulb temperatures.*?\n'
        r'.*?Daily Avg\s+([\d\s.\-]+)',
        txt, re.DOTALL
    )
    if m:
        vals = [float(x) for x in m.group(1).split()
                if re.match(r'-?\d+\.?\d*', x)]
        out['monthly_avg_temp'] = vals[:12]

    m2 = re.search(
        r'Monthly Statistics for Wind Speed.*?\n'
        r'.*?Daily Avg\s+([\d\s.\-]+)',
        txt, re.DOTALL
    )
    if m2:
        vals = [float(x) for x in m2.group(1).split()
                if re.match(r'-?\d+\.?\d*', x)]
        out['monthly_avg_wind_ms'] = vals[:12]

    # Design wind WS010
    m3 = re.search(r'Extremes\t([\d.]+)\t([\d.]+)\t([\d.]+)', txt)
    if m3:
        out['design_wind_ws010_ms'] = float(m3.group(1))

    # Degree days
    m4 = re.search(r'(\d+) annual.*?cooling degree-days \(10', txt)
    m5 = re.search(r'(\d+) annual.*?heating degree-days \(10', txt)
    if m4: out['annual_CDD10'] = int(m4.group(1))
    if m5: out['annual_HDD10'] = int(m5.group(1))

    return out


def epw_monthly_peaks(path):
    """Extract monthly peak values and severe-day counts from EPW."""
    rows = []
    with open(path, 'r', errors='replace') as f:
        for i, line in enumerate(f):
            if i < 8:
                continue
            fields = line.strip().split(',')
            if len(fields) < 34:
                continue
            rows.append(fields)

    daily = defaultdict(lambda: {'temps': [], 'wind': [], 'precip': 0.0})
    for r in rows:
        m, d = int(r[1]), int(r[2])
        key = (m, d)
        try:
            daily[key]['temps'].append(float(r[6]))
            daily[key]['wind'].append(float(r[21]))
            p = float(r[33])
            if p < 900:
                daily[key]['precip'] += p
        except (ValueError, IndexError):
            pass

    monthly = {}
    for mi in range(12):
        mo = mi + 1
        keys = [(mo, d) for d in range(1, DAYS_IN_MONTH[mi] + 1)]
        peak_rain = peak_wind = 0.0
        min_temp = 99.0
        dr2 = dr10 = dw35 = dw50 = dc5 = dc0 = 0

        for key in keys:
            v = daily.get(key, {'temps': [15.0], 'wind': [3.0], 'precip': 0.0})
            rain = v['precip']
            wmax = max(v['wind']) * 3.6 if v['wind'] else 0.0
            tmin = min(v['temps']) if v['temps'] else 15.0

            if rain > peak_rain:  peak_rain = rain
            if wmax > peak_wind:  peak_wind = wmax
            if tmin < min_temp:   min_temp  = tmin

            if rain > 2:   dr2  += 1
            if rain > 10:  dr10 += 1
            if wmax > 35:  dw35 += 1
            if wmax > 50:  dw50 += 1
            if tmin < 5:   dc5  += 1
            if tmin < 0:   dc0  += 1

        monthly[mo] = {
            'pr':   round(peak_rain, 1),
            'pw':   round(peak_wind, 1),
            'pt':   round(min_temp, 1),
            'dr2':  dr2,  'dr10': dr10,
            'dw35': dw35, 'dw50': dw50,
            'dc5':  dc5,  'dc0':  dc0,
        }
    return monthly


def build_dataset(epw_dir, stat_dir):
    """Build the full merged dataset from all EPW and STAT files."""
    epw_files = sorted([
        f for f in os.listdir(epw_dir)
        if f.startswith('TMY3_NZ_') and f.endswith('.epw')
    ])

    all_data = {}
    for fname in epw_files:
        code = fname.replace('TMY3_NZ_', '').replace('.epw', '')
        epw_path  = os.path.join(epw_dir,  fname)
        stat_path = os.path.join(stat_dir, fname.replace('.epw', '.stat'))

        print(f"  Processing {code}...", end=' ')

        meta, rain, wind, temp, rh = parse_epw(epw_path)
        peaks = epw_monthly_peaks(epw_path)

        stat = {}
        if os.path.exists(stat_path):
            stat = parse_stat(stat_path)
        else:
            print(f"(no STAT file)", end=' ')

        mw_kph = [round(x * 3.6, 1) for x in stat.get('monthly_avg_wind_ms', [])]

        all_data[code] = {
            'city':   meta['city'],
            'region': meta['region'],
            'lat':    meta['lat'],
            'lon':    meta['lon'],
            'r':  rain,
            'w':  wind,
            't':  temp,
            'h':  [int(x) for x in rh],
            'mt': stat.get('monthly_avg_temp', []),
            'mw': mw_kph,
            'hdd': stat.get('annual_HDD10'),
            'cdd': stat.get('annual_CDD10'),
            'dw':  stat.get('design_wind_ws010_ms'),
            'mp': {
                k: [peaks[m][k] for m in range(1, 13)]
                for k in ['pr', 'pw', 'pt', 'dr2', 'dr10', 'dw35', 'dw50', 'dc5', 'dc0']
            },
        }

        ann_rain = sum(rain)
        print(f"OK — {meta['city']}, {ann_rain:.0f}mm/yr")

    return all_data


def main():
    parser = argparse.ArgumentParser(
        description='Build rainin_data.json from NIWA TMY3 EPW/STAT files.'
    )
    parser.add_argument('--epw',  default='.', help='Directory containing EPW files')
    parser.add_argument('--stat', default='.', help='Directory containing STAT files')
    parser.add_argument('--out',  default='rainin_data.json', help='Output JSON file')
    parser.add_argument('--gzip', action='store_true', help='Also write a .gz version')
    args = parser.parse_args()

    print(f"RainIn pre-processor")
    print(f"EPW dir:  {args.epw}")
    print(f"STAT dir: {args.stat}")
    print(f"Output:   {args.out}\n")

    data = build_dataset(args.epw, args.stat)
    out_json = json.dumps(data, separators=(',', ':'))

    with open(args.out, 'w') as f:
        f.write(out_json)

    print(f"\nDone — {len(data)} stations")
    print(f"Raw:  {len(out_json):,} bytes ({len(out_json)/1024:.1f} KB)")

    if args.gzip:
        gz_path = args.out + '.gz'
        with gzip.open(gz_path, 'wb') as f:
            f.write(out_json.encode())
        gz_size = os.path.getsize(gz_path)
        print(f"Gzip: {gz_size:,} bytes ({gz_size/1024:.1f} KB) → {gz_path}")


if __name__ == '__main__':
    main()
