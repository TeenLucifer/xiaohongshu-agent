from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    print(root / "src")


if __name__ == "__main__":
    main()
