import streamlit as st
import pandas as pd
from io import BytesIO

#SetupPage
byfile = st.Page(
     page="byfile.py",
     title="Versi 2",
     icon="📁",
)

discount = st.Page(
     page="discount.py",
     title="Discount",
     icon="💸",
)

bylist = st.Page(
     page="bylist.py",
     title="Versi 1",
     icon="📃",
     default=True,
)

salessuport = st.Page(
     page="salessupport.py",
     title="Sales Support",
     icon="📈",
)

TasKarung = st.Page(
     page="Tas&Karung.py",
     title="Versi Tas&Karung",
     icon="📁",
)

FotoKT = st.Page(
     page="bylist2_fotokt.py",
     title="Versi 1.1 (FotoKT)",
     icon="📁",
)

pg = st.navigation({
     "Choose": [bylist, byfile, salessuport, discount, TasKarung, FotoKT],
})

pg.run()