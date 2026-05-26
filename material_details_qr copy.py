from member import *
from param import ClearSelection
from job import ProcessJob

def run_sel_mem():
    ClearSelection()
    mem_list = MultiMemberLocate("Select members to get details")
    for mem in mem_list:
        for attr in dir(mem):
            if not attr.startswith("_"):
                try:
                    value = getattr(mem, attr)
                    if attr == "material" and callable(value):
                        try:
                            result = value()
                            print(attr + ":")
                            for sub_attr in dir(result):
                                if not sub_attr.startswith("_"):
                                    try:
                                        sub_value = getattr(result, sub_attr)
                                        if not callable(sub_value):
                                            print("  " + sub_attr + ": " + (str(sub_value) if sub_value else "N/A"))
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    elif attr in ("left", "right") and not callable(value):
                        print(attr + ":")
                        for sub_attr in dir(value):
                            if not sub_attr.startswith("_"):
                                try:
                                    sub_value = getattr(value, sub_attr)
                                    if not callable(sub_value):
                                        print("  " + sub_attr + ": " + (str(sub_value) if sub_value else "N/A"))
                                except Exception:
                                    pass
                    elif not callable(value):
                        print(attr + ": " + (str(value) if value else "N/A"))
                except Exception:
                    pass
        break

if __name__ == '__main__':
    run_sel_mem()