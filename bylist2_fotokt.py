import pandas as pd
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import streamlit as st
import textwrap
import zipfile
from google.oauth2 import service_account
import gspread
from googleapiclient.discovery import build

st.set_page_config("Sukses Jaya - Create Photos")

# Path ke file getlink.json Anda
SERVICE_ACCOUNT_FILE = st.secrets["secretkey"]
# Scopes yang diperlukan untuk Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']
# Autentikasi menggunakan service account
credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# Membangun layanan Google Drive API
service = build('drive', 'v3', credentials=credentials)
client = gspread.authorize(credentials)


# --- Streamlit Buttons ---
# start = st.button("Update Photos")

@st.cache_data
def get_data_from_google():
    with st.spinner("Getting data from Google Sheets..."):
        sheet = client.open_by_key("18t23AKiAQmK4A4dmkwqYTOGj4gNuFMEAsBpY50zJLNY")
        
        # Database
        worksheet = sheet.worksheet('FotoKT')
        database = pd.DataFrame(worksheet.get_all_records())
        
        # Catalogue
        worksheet = sheet.worksheet('CatalogueUpdate')
        catalogue = pd.DataFrame(worksheet.get_all_records())
        catalogue['ItemCode'] = catalogue['ItemCode'].astype(str)
        
        return database, catalogue

st.session_state.database, st.session_state.catalogue = get_data_from_google()

database = st.session_state.database
file_catalogue = st.session_state.catalogue
file_catalogue['U_Kategori'] = file_catalogue['U_Kategori'].astype(str)

# # --- Google Drive Image Fetching ---
# if start:
#     def list_files_in_folder_recursive(folder_id):
#         file_data = []
#         page_token = None
#         while True:
#             response = service.files().list(
#                 q=f"'{folder_id}' in parents",
#                 spaces='drive',
#                 fields="nextPageToken, files(id, name, mimeType, createdTime)",
#                 pageToken=page_token
#             ).execute()
#             for item in response.get('files', []):
#                 if item['mimeType'].startswith('image/'):
#                     file_data.append({
#                         'Name': item['name'],
#                         'Link': f"https://drive.google.com/uc?export=download&id={item['id']}",
#                         'Upload Date': item['createdTime']
#                     })
#                 elif item['mimeType'] == 'application/vnd.google-apps.folder':
#                     file_data.extend(list_files_in_folder_recursive(item['id']))
#             page_token = response.get('nextPageToken')
#             if not page_token:
#                 break
#         return file_data

#     FOLDER_ID = '1UmZBAd1pC7pUi_0B7je-fFtZHY6uRYsJ'
#     file_data = list_files_in_folder_recursive(FOLDER_ID)
#     df_foto = pd.DataFrame(file_data)

#     # Remove all listed extensions from filenames
#     ext_pattern = r"(\.jpg|\.jpeg|\.JPEG|\.mp4|\.Ink|\.png|\.ini|\.jfif)$"
#     df_foto['ItemCode'] = df_foto['Name'].str.replace(ext_pattern, '', regex=True)
#     df_foto.rename(columns={'ItemCode':'Verse1'}, inplace=True)
#     df_foto['MatchStatus'] = df_foto['Verse1'].apply(lambda x: 'Match' if x in file_catalogue['ItemCode'].values else 'Tidak Match')
#     df_foto['ItemCode'] = df_foto.apply(lambda row: row['Verse1'] if row['MatchStatus']=='Match' else row['Verse1'].split(' ')[0], axis=1)
#     df_foto = df_foto.sort_values(by='Upload Date', ascending=False)

#     # Update Google Sheet
#     sheet = client.open_by_key("18t23AKiAQmK4A4dmkwqYTOGj4gNuFMEAsBpY50zJLNY")
#     worksheet = sheet.worksheet('FotoKT')
#     worksheet.update([df_foto.columns.values.tolist()] + df_foto.values.tolist())

#     st.success("Success Update Data")
#     st.dataframe(df_foto)
#     st.session_state.database = get_data_from_google()[0]
#     st.session_state.catalogue = get_data_from_google()[1]

# --- Streamlit UI ---
st.title("Hai Everyone! made by: V")
st.write("Upload Excel with columns: 'ItemCode', 'List', 'Harga'")
st.warning("Update Photo may take ± 10 minutes depending on internet speed")

file_upload = st.file_uploader("Upload File", type=["xlsx","xls","csv"])

if not file_upload:
    st.warning("Please upload a file.")
    st.stop()

# Read uploaded file
try:
    if file_upload.name.endswith(('.xls', '.xlsx')):
        file_user = pd.read_excel(file_upload)
    else:
        file_user = pd.read_csv(file_upload)
    file_user['ItemCode'] = file_user['ItemCode'].astype(str)
    file_user['Harga'] = file_user['Harga'].astype(str)
    start2 = st.button("Start Now")
except Exception as e:
    st.error(f"Error reading files: {e}")
    st.stop()

# --- Image Generation ---
if start2:
    with st.spinner("Processing..."):
        database['ItemCode'] = database['ItemCode'].astype(str).str.upper()
        file_user['ItemCode'] = file_user['ItemCode'].astype(str).str.upper()
        database['Upload Date'] = pd.to_datetime(database['Upload Date'], errors='coerce')
        database = database.loc[database.groupby('ItemCode')['Upload Date'].idxmax()]

        # Merge uploaded file with image links
        selected_df = pd.merge(file_user, database[['ItemCode','Link']], on='ItemCode', how='left')
        df_kosong = selected_df[selected_df['Link'].isna()]
        selected_df = selected_df[~selected_df['Link'].isna()]

        # Merge with catalogue for other info
        selected_df = pd.merge(selected_df, file_catalogue[['ItemCode','ItemName','Uom','IsiCtn','U_Kategori']], on='ItemCode', how='left')

        st.write("Images to create:")
        st.dataframe(selected_df)
        st.write("Not found in Google Drive:")
        st.dataframe(df_kosong)

        # Fonts
        font_path = "./Poppins-Regular.ttf"
        font_harga = ImageFont.truetype("./Poppins-SemiBold.ttf", size=20)
        font_regular = ImageFont.truetype(font_path, size=20)

        def wrap_text(text, font, max_width):
            wrapped_text = textwrap.fill(text, width=max_width // (font.getbbox('a')[2] - font.getbbox('a')[0]))
            return wrapped_text.splitlines()

        def add_image(img_url, row):
            try:
                template = Image.new("RGBA",(800,1200),"white")
                response = requests.get(img_url, timeout=15)
                if response.status_code != 200:
                    raise ValueError(f"HTTP {response.status_code}")
                img_bytes = BytesIO(response.content)
                img = Image.open(img_bytes).convert("RGBA")
                img = img.resize((750,750))
                image_x = (template.width - img.width)//2
                image_y = 25
                template.paste(img,(image_x,image_y))
            except Exception as e:
                st.error(f"Error loading image: {e} {row['ItemCode']}")
            return template

        def add_text(template, draw, row):
            item_code = row['ItemCode']
            item_name = row['ItemName']
            try:
                price = float(row['Harga'])
                harga_jual = f"Rp. {price:,.0f} / {row['Uom']}"
            except:
                harga_jual = f"Rp. - / {row['Uom']}"
            ctn = f"Isi Karton: {int(row['IsiCtn'])} {row['Uom']}" if pd.notna(row['IsiCtn']) else "N/A"

            lines_item_code = wrap_text(item_code, font_regular, 450)
            lines_item_name = wrap_text(item_name, font_regular, 450)
            lines_harga_jual = wrap_text(harga_jual, font_harga, 450)
            lines_ctn = wrap_text(ctn, font_regular, 450)

            all_lines = lines_item_code + lines_item_name + lines_harga_jual + lines_ctn

            # Background
            background_width = 735
            background_margin = 10
            corner_radius = 15
            x_position = 32.5
            y_start = 825
            total_text_height = sum(draw.textbbox((0,0),line,font=font_regular)[3] for line in all_lines)
            total_height = total_text_height + (len(all_lines)+1)*2*background_margin

            # Draw rounded rectangle
            draw.rounded_rectangle(
                [(x_position-background_margin, y_start), (x_position+background_width+background_margin, y_start+total_height)],
                fill=(255, 225, 135), radius=corner_radius
            )

            y_offset = y_start + background_margin
            for line in all_lines:
                if line in lines_harga_jual:
                    font = font_harga
                else:
                    font = font_regular
                text_width, text_height = draw.textbbox((0,0), line, font=font)[2:4]
                text_x = x_position + (background_width - text_width)//2
                draw.text((text_x, y_offset), line, font=font, fill="black")
                y_offset += text_height + 2*background_margin

        # --- Generate Images & ZIP ---
        category_dict = {}
        image_paths = []

        for _, row in selected_df.iterrows():
            img_template = add_image(row['Link'], row)
            draw = ImageDraw.Draw(img_template)
            add_text(img_template, draw, row)

            buf = BytesIO()
            img_template.save(buf, format='PNG')
            buf.seek(0)
            file_name = f"{row['ItemCode']}.png"
            image_paths.append((file_name, buf.getvalue()))
            category = row['List']
            if category not in category_dict:
                category_dict[category] = []
            category_dict[category].append((file_name, buf.getvalue()))

        if image_paths:
            st.image(image_paths[0][1])

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for category, files in category_dict.items():
                for file_name, image_data in files:
                    file_path = f"{category}/{file_name}"
                    zipf.writestr(file_path, image_data)
        zip_buffer.seek(0)

        st.download_button(
            label="Download ZIP",
            data=zip_buffer,
            file_name="Ready_to_Upload.zip",
            mime="application/zip"
        )