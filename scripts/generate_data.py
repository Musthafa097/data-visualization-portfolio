"""Generates the synthetic, deliberately messy retail dataset used in this project.
Usage: python generate_data.py [output.csv]   (seeded, so output is reproducible)
"""
import sys, zlib
import numpy as np, pandas as pd, random
from datetime import date, timedelta

rng = np.random.default_rng(42)
random.seed(42)
N = 20000

# Product catalogue: (category, product, unit_cost, unit_price)
catalogue = [
    ("Electronics","Wireless Headphones",32,79.99),("Electronics","Smart Speaker",28,59.99),
    ("Electronics","Tablet 10in",110,229.00),("Electronics","Phone Charger",4,14.99),
    ("Electronics","Bluetooth Keyboard",15,39.99),("Electronics","Webcam HD",18,44.99),
    ("Clothing","Winter Jacket",35,89.00),("Clothing","Running Shoes",30,74.99),
    ("Clothing","Cotton T-Shirt",5,14.00),("Clothing","Denim Jeans",16,49.00),
    ("Clothing","Wool Scarf",7,19.99),
    ("Home & Kitchen","Air Fryer",42,99.99),("Home & Kitchen","Coffee Maker",25,64.99),
    ("Home & Kitchen","Non-stick Pan Set",20,54.99),("Home & Kitchen","Vacuum Cleaner",70,149.00),
    ("Home & Kitchen","Bedding Set",18,44.99),
    ("Sports & Outdoors","Yoga Mat",6,22.00),("Sports & Outdoors","Camping Tent",48,119.00),
    ("Sports & Outdoors","Dumbbell Set",26,59.99),("Sports & Outdoors","Water Bottle",3,12.99),
    ("Beauty","Face Moisturiser",6,24.99),("Beauty","Hair Dryer",19,49.99),
    ("Beauty","Perfume 50ml",14,45.00),("Beauty","Electric Toothbrush",17,39.99),
    ("Books & Stationery","Hardback Novel",4,14.99),("Books & Stationery","Notebook Pack",2,8.99),
    ("Books & Stationery","Fountain Pen",9,24.99),
]
cat_weights = {"Electronics":0.26,"Clothing":0.22,"Home & Kitchen":0.20,"Sports & Outdoors":0.12,"Beauty":0.12,"Books & Stationery":0.08}

regions = {
 "Northern Ireland":["Belfast","Derry","Lisburn","Newry"],
 "London":["London"],
 "North West":["Manchester","Liverpool","Preston"],
 "Scotland":["Glasgow","Edinburgh","Aberdeen"],
 "Midlands":["Birmingham","Leicester","Nottingham"],
 "Wales":["Cardiff","Swansea"],
 "South West":["Bristol","Plymouth","Exeter"],
}
reg_w = [0.10,0.24,0.16,0.12,0.15,0.07,0.16]
segments = ["Consumer","Small Business","Corporate"]; seg_w=[0.62,0.25,0.13]
channels = ["Online","In-Store","Mobile App"]; ch_w=[0.48,0.34,0.18]
pay = ["Card","PayPal","Cash","Gift Card"]; pay_w=[0.58,0.22,0.12,0.08]

# customers
n_cust = 3800
cust_ids = [f"C{10000+i}" for i in range(n_cust)]
cust_seg = {c: rng.choice(segments,p=seg_w) for c in cust_ids}
cust_region = {}
for c in cust_ids:
    r = rng.choice(list(regions.keys()),p=reg_w)
    cust_region[c]=(r, random.choice(regions[r]))

# dates 2024-01-01 .. 2026-10-31 with seasonality + growth
start = date(2024,1,1); end = date(2026,10,31)
days = (end-start).days+1
all_days = [start+timedelta(d) for d in range(days)]
w = []
for d in all_days:
    m = d.month
    season = {1:0.85,2:0.8,3:0.9,4:0.95,5:1.0,6:1.0,7:0.95,8:0.95,9:1.0,10:1.1,11:1.45,12:1.6}[m]
    growth = 1 + 0.35*((d-start).days/days)
    dow = 1.15 if d.weekday()>=5 else 1.0
    w.append(season*growth*dow)
w = np.array(w); w/=w.sum()
order_dates = rng.choice(len(all_days), size=N, p=w)
order_dates = [all_days[i] for i in order_dates]

cats = list(cat_weights.keys()); cw=[cat_weights[c] for c in cats]
by_cat = {c:[p for p in catalogue if p[0]==c] for c in cats}

rows=[]
for i in range(N):
    cust = rng.choice(cust_ids)
    reg, city = cust_region[cust]
    cat = rng.choice(cats,p=cw)
    # seasonal tilt: clothing/jackets in winter handled loosely
    _,prod,cost,price = random.choice(by_cat[cat])
    d = order_dates[i]
    if prod in ("Winter Jacket","Wool Scarf") and d.month in (5,6,7,8) and random.random()<0.7:
        _,prod,cost,price = random.choice(by_cat["Clothing"])
    qty = int(rng.choice([1,2,3,4,5],p=[0.55,0.25,0.12,0.05,0.03]))
    disc = float(rng.choice([0,0.05,0.10,0.15,0.20],p=[0.55,0.15,0.15,0.10,0.05]))
    ch = rng.choice(channels,p=ch_w)
    rows.append(dict(
        OrderID=f"ORD-{100000+i}",
        OrderDate=d,
        CustomerID=cust,
        CustomerSegment=cust_seg[cust],
        Region=reg, City=city,
        Category=cat, Product=prod,
        Quantity=qty, UnitPrice=price, UnitCost=cost,
        DiscountPct=disc,
        SalesChannel=ch,
        PaymentMethod=rng.choice(pay,p=pay_w),
        ReturnedFlag="Yes" if random.random()<0.06 else "No",
    ))
df = pd.DataFrame(rows)

# realistic cost ratios by category (so margins differ by category)
ratio = {"Electronics":0.70,"Clothing":0.42,"Home & Kitchen":0.62,"Sports & Outdoors":0.55,"Beauty":0.36,"Books & Stationery":0.50}
prod_noise = {p[1]: 1+((zlib.crc32(p[1].encode())%11)-5)/100 for p in catalogue}
df["UnitCost"] = [round(r.UnitPrice*ratio[r.Category]*prod_noise[r.Product],2) for r in df.itertuples()]
# ---------- inject realistic dirt ----------
raw = df.copy()
raw["OrderDate"] = raw["OrderDate"].astype(object)

# 1. mixed date formats
idx = rng.choice(N, size=int(N*0.30), replace=False)
for i in idx:
    d = df.loc[i,"OrderDate"]
    raw.at[i,"OrderDate"] = d.strftime("%d/%m/%Y")
idx2 = rng.choice(N, size=int(N*0.15), replace=False)
for i in idx2:
    d = df.loc[i,"OrderDate"]
    raw.at[i,"OrderDate"] = d.strftime("%Y-%m-%d")
idx3 = rng.choice(N, size=int(N*0.10), replace=False)
for i in idx3:
    d = df.loc[i,"OrderDate"]
    raw.at[i,"OrderDate"] = d.strftime("%d-%b-%Y")
# remaining stay as ISO-like; make everything string
raw["OrderDate"] = raw["OrderDate"].apply(lambda x: x if isinstance(x,str) else x.strftime("%Y-%m-%d"))

# 2. inconsistent text (case / whitespace / typos)
def messy(s):
    r = random.random()
    if r<0.04: return s.upper()
    if r<0.08: return s.lower()
    if r<0.11: return "  "+s+" "
    return s
for col in ["Region","Category","SalesChannel","CustomerSegment"]:
    raw[col] = raw[col].apply(messy)
typo_idx = rng.choice(N, size=120, replace=False)
for i in typo_idx:
    v = raw.at[i,"Category"].strip().lower()
    if v=="electronics": raw.at[i,"Category"]="Electronis"
    elif v=="clothing": raw.at[i,"Category"]="Clothng"
raw["Region"] = raw["Region"].replace({"London":"london "}) # extra variants
yn = {"Yes":["Yes","Y","yes","TRUE"],"No":["No","N","no","FALSE"]}
raw["ReturnedFlag"] = raw["ReturnedFlag"].apply(lambda v: random.choice(yn[v]) if random.random()<0.25 else v)

# 3. missing values
for col,frac in [("CustomerSegment",0.03),("City",0.02),("PaymentMethod",0.025),("DiscountPct",0.04),("SalesChannel",0.015)]:
    m = rng.choice(N,size=int(N*frac),replace=False)
    raw.loc[m,col]=np.nan
m = rng.choice(N,size=60,replace=False); raw.loc[m,"UnitPrice"]=np.nan

# 4. bad numerics: negative qty, price stored as text with currency symbol, outliers
raw["UnitPrice"] = raw["UnitPrice"].astype(object)
pi = rng.choice(N,size=300,replace=False)
for i in pi:
    v = raw.at[i,"UnitPrice"]
    if pd.notna(v): raw.at[i,"UnitPrice"] = f"£{v:,.2f}"
neg = rng.choice(N,size=40,replace=False); raw.loc[neg,"Quantity"]=-raw.loc[neg,"Quantity"]
zero = rng.choice(N,size=25,replace=False); raw.loc[zero,"Quantity"]=0
out = rng.choice(N,size=15,replace=False); raw.loc[out,"Quantity"]=raw.loc[out,"Quantity"].abs()*100
# discount as whole number occasionally (e.g. 10 instead of 0.10)
dd = rng.choice(N,size=200,replace=False)
for i in dd:
    v = raw.at[i,"DiscountPct"]
    if pd.notna(v) and v>0: raw.at[i,"DiscountPct"]=v*100

# 5. duplicates (exact repeats of earlier rows)
dups = raw.sample(n=550, random_state=7)
raw = pd.concat([raw,dups], ignore_index=True).sample(frac=1,random_state=3).reset_index(drop=True)

out = sys.argv[1] if len(sys.argv) > 1 else "retail_sales_raw.csv"
raw.to_csv(out, index=False)
print(raw.shape)
print(raw.head(8).to_string())
print(raw.isna().sum())
