import os
import pandas as pd
import yfinance as yf


def generate_data(stock: str, root_folder: str):
    """
    Generate data for the given stock and save it to the root folder.
    For each stock, the following files are generated:
    - <stock>_open.csv
    - <stock>_high.csv
    - <stock>_low.csv
    - <stock>_close.csv
    - <stock>_volume.csv
    """
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)

    data = yf.download(stock, start="2020-01-01", end="2020-12-31")
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df = pd.DataFrame(data[col].reset_index())
        df.columns = ["timestamp", "value"]
        df["timestamp"] = df["timestamp"].astype(int) // 10**9

        df.to_csv(
            os.path.join(
                root_folder,
                f"{stock}_{col.lower()}.csv",
            ),
            index=False,
        )


if __name__ == "__main__":
    generate_data("AAPL", "./data")
    generate_data("GOOGL", "./data")
    generate_data("MSFT", "./data")

    print("Data generated successfully.")
