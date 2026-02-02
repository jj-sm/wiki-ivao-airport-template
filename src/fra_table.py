import requests
import os
import json
from dotenv import load_dotenv
from typing import List, Generator

import requests_cache

requests_cache.install_cache(
    cache_name="ivao_api_cache",
    backend="sqlite",
    expire_after=60*60
)

load_dotenv()
IVAO_API_KEY = os.getenv("IVAO_API_KEY")
ATC_1 = os.getenv("ATC_1")
ATC_2 = os.getenv("ATC_2")
ATC_3 = os.getenv("ATC_3")
ATC_4 = os.getenv("ATC_4")
ATC_5 = os.getenv("ATC_5")
ATC_6 = os.getenv("ATC_6")
ATC_7 = os.getenv("ATC_7")
ATC_8 = os.getenv("ATC_8")
ATC_9 = os.getenv("ATC_9")
ATC_10 = os.getenv("ATC_10")

rank_enum = enumerate([
    ATC_1, ATC_2, ATC_3, ATC_4, ATC_5,
    ATC_6, ATC_7, ATC_8, ATC_9, ATC_10
], start=1)

RANK_MAP = dict((k, v) for k, v in rank_enum if v)


def request_airport_atc_positions(icao_code: str) -> Generator:
    url = f"https://api.ivao.aero/v2/airports/{icao_code}/ATCPositions"
    headers = {
        "apiKey": IVAO_API_KEY,
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data: List[dict] = response.json()

    for position in data:
        yield position


def request_fra_info(position_id: int) -> list:
    url = f"https://api.ivao.aero/v2/ATCPositions/{position_id}/fras?page=1&perPage=20&members=false&positions=true"
    headers = {
        "apiKey": IVAO_API_KEY,
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data: dict = response.json()

    data_items = data.get("items", [])

    available_fras = set()
    is_active_count = 0
    for fra in data_items:
        fra_id = fra.get("minAtc")
        is_active = fra.get("active")
        if not is_active:
            is_active_count += 1
        available_fras.add(fra_id)
    
    if is_active_count == len(data_items):
        print(f"[WARN]: All FRAs for position ID {position_id} are inactive.")    

    return sorted(list(available_fras))


def make_markdown_table(data_dict: list, icao: str) -> None:
    headers = ["Indicativo", "Frecuencia", "FRA", "Observaciones"]
    out_file_lines = []
    out_file_lines.append("| " + " | ".join(headers) + " |")
    out_file_lines.append("|" + "|".join([":---:"] * len(headers)) + "|")

    for entry in data_dict:
        ivao_cs = entry['ivao_callsign']
        indicativo_str = f"`{ivao_cs}` <br> <em>{entry['atc_callsign']}</em>"
        frecuencia_str = f"{entry['frequency']:.3f} MHz"
        fra_str = "<br>".join(
            f"[![{indicativo_str}]({RANK_MAP.get(fra, fra)})](https://atc.ivao.aero/fras?filter={ivao_cs})"
            for fra in entry['available_fras']
        )
        observations_str = ""
        out_file_lines.append(
            f"| {indicativo_str} | {frecuencia_str} | {fra_str} | {observations_str} |"
        )
    out_md = "\n".join(out_file_lines)
    output_filename = f"{icao}_atc_positions.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(out_md)
    print(f"Markdown table saved to {output_filename}")
        


def order_data_by_position(data_dict: list) -> list:
    priority_order = {
        "DEL": 1,
        "GND": 2,
        "TWR": 3,
        "APP": 4,
        "CTR": 5,
        "FSS": 6,
    }

    def sort_key(entry: dict):
        callsign = entry.get("ivao_callsign", "")
        pos_priority = 99
        position_type = ""
        for key, value in priority_order.items():
            if callsign.endswith(f"_{key}"):
                pos_priority = value
                position_type = key
                break

        underscore_count = callsign.count("_")

        sector_len = 0
        if position_type and callsign != f"{callsign.split('_')[0]}_{position_type}":
            sector = callsign.replace(f"_{position_type}", "").split("_", 1)[-1]
            sector_len = len(sector)

        return (
            pos_priority,
            underscore_count,
            sector_len,
            callsign
        )

    return sorted(data_dict, key=sort_key)


def main():
    if not IVAO_API_KEY:
        print("Error: IVAO_API_KEY not found in environment variables.")
        return
    else:
        ICAO = input("Enter ICAO code: ").strip().upper()
        print(f"Fetching ATC positions for airport {ICAO}...")
        try:
            out_data = []
            for atc_position in request_airport_atc_positions(ICAO):
                atc_composePosition = atc_position.get("composePosition")
                atcCallsign = atc_position.get("atcCallsign")
                frequency = atc_position.get("frequency")
                atc_id = atc_position.get("id")
                print(f"\nFound ATC Position ID: {atc_id} - {atc_composePosition}")

                fra_info = request_fra_info(atc_id)
                out_data.append({
                    "ivao_callsign": atc_composePosition,
                    "atc_callsign": atcCallsign,
                    "frequency": frequency,
                    "available_fras": fra_info
                })
            out_json = json.dumps(out_data, indent=4)
            output_filename = f"{ICAO}_atc_positions.json"
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(out_json)
            print(f"Data saved to {output_filename}")

            try:
                data_md = order_data_by_position(out_data)
                make_markdown_table(data_md, ICAO)
            except Exception as e:
                print(f"Error generating markdown table: {e}")

        except requests.HTTPError as e:
            print(f"HTTP Error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
    

if __name__ == "__main__":
    main()