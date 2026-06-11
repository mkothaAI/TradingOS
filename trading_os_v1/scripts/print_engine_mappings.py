from trading_os_v1.engines import load_all_engines
from pathlib import Path


def main():
    md = Path(__file__).resolve().parents[2] / 'docs' / 'engine-mapping' / 'varsity-to-trading_os_v1.md'
    engines = load_all_engines(str(md))
    for name, eng in engines.items():
        print(f"Engine: {name} — mappings: {len(eng.mappings)}")
        if eng.mappings:
            first = eng.mappings[0]
            print(f"  - First: {first.principle} | source={first.source} | status={first.status}")


if __name__ == '__main__':
    main()
