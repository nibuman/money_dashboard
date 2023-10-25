import datetime

import pandas as pd
import piecash
from dateutil.relativedelta import relativedelta

book = piecash.open_book("/home/nick/Documents/Money/GnuCash/NB_accounts_2023.gnucash")
root = book.root_account  # select the root_account

assets = root.children(name="Assets")  # select child account by name
savings = assets.children(name="Savings & Investments")


date = datetime.datetime.now().date()
asset_accounts = [acc.name for acc in assets.children if acc.get_balance(recurse=True) and not acc.hidden]
time_series = {"date": []}

while date >= datetime.date(year=2018, month=1, day=1):
    time_series["date"].append(date)
    date -= relativedelta(months=1)
for account in asset_accounts:
    time_series[account] = [
        assets.children(name=account).get_balance(recurse=True, at_date=date) for date in time_series["date"]
    ]

df = pd.DataFrame(time_series).set_index("date")
print(df)

df.to_csv("gnucash_export.csv")
