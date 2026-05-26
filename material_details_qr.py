# -*- coding: utf-8 -*-
from member import *
from param import ClearSelection
from job import ProcessJob
from fractions import Fraction
import os
import json
import subprocess

MEM_ATTRS = ("grade", "is_galvanized", "piecemark", "section_size", "type", "thick", "depth")

# ── Path to your Python 3.10 interpreter and the generator script ──────────
PYTHON3   = r"C:\Program Files\Python310\python.exe"          # adjust if needed
GEN_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "generate_qr_sheet.py")
# ───────────────────────────────────────────────────────────────────────────


def to_feet_inches(decimal_inches):
    feet = int(decimal_inches // 12)
    remaining = decimal_inches % 12
    whole_in = int(remaining)
    frac = remaining - whole_in
    frac_str = ""
    if frac:
        f = Fraction(frac).limit_denominator(16)
        frac_str = " " + str(f)
    return str(feet) + "-" + str(whole_in) + frac_str


def collect_member_data(mem):
    data = {}
    for attr in MEM_ATTRS:
        try:
            value = getattr(mem, attr)
            data[attr] = str(value) if value is not None else "N/A"
        except Exception:
            data[attr] = "N/A"

    try:
        data["length"] = to_feet_inches(mem.length)
    except Exception:
        data["length"] = "N/A"

    try:
        mat = mem.material()
        data["weight"] = "{:.2f}".format(float(mat.weight)) if mat.weight else "N/A"
    except Exception:
        data["weight"] = "N/A"

    for side in ("left", "right"):
        try:
            side_obj = getattr(mem, side)
            data[side + "_conn"] = str(side_obj.input_conn_type) if side_obj.input_conn_type else "N/A"
        except Exception:
            data[side + "_conn"] = "N/A"

    return data


def get_output_dir():
    base = None
    try:
        job = ProcessJob()
        base = job.path
    except Exception:
        pass
    if not base:
        try:
            base = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            base = os.path.expanduser("~")
    out = os.path.join(base, "QR_Codes")
    if not os.path.exists(out):
        os.makedirs(out)
    return out


def run_sel_mem():
    # ClearSelection()
    mem_list = MultiMemberLocate("Select members to get details")

    if not mem_list:
        print("No members selected.")
        return

    output_dir = get_output_dir()
    all_data = []

    for mem in mem_list:
        data = collect_member_data(mem)
        all_data.append(data)
        print("Collected: " + data.get("piecemark", "UNKNOWN"))

    # Save JSON for the Python 3.10 script to read
    json_path = os.path.join(output_dir, "members.json")
    with open(json_path, "w") as f:
        json.dump(all_data, f, indent=2)

    print("\nSaved member data to: " + json_path)
    print("Launching QR sheet generator...")

    try:
        subprocess.Popen([PYTHON3, GEN_SCRIPT, json_path])
        print("Generator launched. Check the QR_Codes folder for output.")
    except Exception as e:
        print("Could not launch generator: " + str(e))
        print("Run manually: " + PYTHON3 + " " + GEN_SCRIPT + " " + json_path)


if __name__ == '__main__':
    run_sel_mem()