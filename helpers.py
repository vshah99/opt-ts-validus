from req_import import *

def load_and_preprocess(refresh=False) -> pd.DataFrame:
    pkl_fp = r"final_input.pkl"
    csv_fp = r"raw_input.csv"

    if os.path.exists(pkl_fp) and not refresh:
        df = pd.read_pickle(pkl_fp)
    else:
        df = pd.read_csv(csv_fp)

        # Remove all columns with only 1 value
        for col in df.columns:
            if len(df[col].unique()) == 1:
                df.drop(col, inplace=True, axis=1)
        # adjusted == unadjusted always, so we can drop the latter. Given we have
        if all(df['adjusted close'] == df['unadjusted']):
            df.drop(columns=['unadjusted'], inplace=True)
        # rename spaces with underscore for easier access: df.adjusted_close rather than df['adjusted close']
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('/', '_').str.lower()
        df['date'] = pd.to_datetime(df['date'])
        df['expiration'] = pd.to_datetime(df['expiration'])

        df.sort_values(['date', 'expiration', 'strike'], ascending=[True, True, True], inplace=True)
        df.to_pickle(pkl_fp)

    return df


_date_pattern = "^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$"
def parse_date(strdt, default="2021-04-30") -> datetime.date:
    if strdt is None:
        strdt = default
    if isinstance(strdt, str) and re.match(_date_pattern, strdt):
        return datetime.strptime(strdt, "%Y-%m-%d")
    raise ValueError("Invalid Date Format")


def base_round(x, base=5):
    return base * round(x / base)