import pandas as pd
import streamlit as st
import plotly.express as px
import statsmodels.api as sm
import sqlite3
from io import BytesIO
import plotly.io as pio
from streamlit.runtime.scriptrunner import RerunException
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# 日本語フォントを登録（パスは適宜変更してください）
pdfmetrics.registerFont(TTFont("IPAexGothic", "ipaexg.ttf"))


import requests
from bs4 import BeautifulSoup

st.set_page_config(
        page_title="My Streamlit App",
        page_icon="📈",
        layout="wide",  # ウィンドウサイズに合わせて広く表示
    )


conn = sqlite3.connect('id_database.db')
id_list = pd.read_sql_query("SELECT * FROM id_table", conn)
conn.close()

conn = sqlite3.connect('physical_rawdata.db')
rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
conn.close()







def get_fig_as_image(fig):
    img_bytes = fig.to_image(format="png")  # 画像をバイナリデータで取得
    return BytesIO(img_bytes)  # バイナリデータをBytesIOでラップ
# 画像サイズ取得

def get_image_dimensions(image_path):
    with Image.open(image_path) as img:
        return img.size  # (width, height)



def get_first_image_url(name):
    # Google画像検索のURLを作成
    query = f"{name.replace(' ', '+')}+野球"
    url = f"https://www.google.com/search?tbm=isch&q={query}"

    # User-Agentを偽装しないとブロックされる
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # リクエスト送信
    response = requests.get(url, headers=headers)

    # ページ解析
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")

    # 最初の画像のURLを取得（通常、1つ目はGoogleロゴなので2つ目を使う）
    if len(img_tags) > 1:
        return img_tags[1]["src"]
    else:
        return "画像が見つかりませんでした。"
    
def save_plots_to_pdf(figlist, name, ja_name, comment):
    pdf_output = BytesIO()
    c = canvas.Canvas(pdf_output, pagesize=letter)
    width, height = letter

    for i in range(0, len(figlist), 2):
        # ページ共通：タイトルとロゴ
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(width / 2, height - 70, name)
        logo_path = "TsukubaLogo.png"
        logo = ImageReader(logo_path)
        c.drawImage(logo, 40, height - 85, width=50, height=50, mask='auto')

        # 上部画像（顔写真）
        url = get_first_image_url(ja_name)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            width2, height2 = img.size
            size = min(width2, height2)
            left = (width2 - size) // 2
            top = (height2 - size) // 2
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            cropped_img = img.crop((left, top, left + size, top + size))
            cropped_img.putalpha(mask)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                cropped_img.save(tmpfile.name, format="PNG")
                top_img_width, top_img_height = get_image_dimensions(tmpfile.name)
                ratio = 50 / top_img_width
                c.drawImage(tmpfile.name, 500, height - 85, width=top_img_width * ratio, height=top_img_height * ratio, mask='auto')

        # 最初のグラフ
        if i < len(figlist):
            img_stream_1 = get_fig_as_image(figlist[i])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile_1:
                tmpfile_1.write(img_stream_1.getvalue())
                tmpfile_1.close()
                img_width, img_height = get_image_dimensions(tmpfile_1.name)
                ratio = (width * 0.8) / img_width
                new_width = width * 0.8
                new_height = img_height * ratio
                x = (width - new_width) / 2
                y1 = height // 2.3
                c.drawImage(tmpfile_1.name, x, y1, width=new_width, height=new_height)

        # 2番目のグラフ or コメント
        if i + 1 < len(figlist):
            # まだ次のグラフがある
            img_stream_2 = get_fig_as_image(figlist[i + 1])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile_2:
                tmpfile_2.write(img_stream_2.getvalue())
                tmpfile_2.close()
                img_width, img_height = get_image_dimensions(tmpfile_2.name)
                ratio = (width * 0.8) / img_width
                new_width = width * 0.8
                new_height = img_height * ratio
                x = (width - new_width) / 2
                c.drawImage(tmpfile_2.name, x, 30, width=new_width, height=new_height)

        else:
            # 最後のページで、奇数番目のグラフが描画された場合 → コメントを一緒に表示
            wrapped_comment = "\n".join([comment[i:i+48] for i in range(0, len(comment), 48)])
            icon_path = "aoki.jpg"
            icon_width = 25
            icon_height = 25
            c.drawImage(icon_path, 50, 300, width=icon_width, height=icon_height, mask='auto')
            c.setFont("IPAexGothic", 12)
            c.drawString(70, 300, "  コメント")
            text = c.beginText(50, 270)
            text.setFont("IPAexGothic", 10)
            text.setLeading(14)
            for line in wrapped_comment.splitlines():
                text.textLine(line)
            c.drawText(text)

        c.showPage()

    # 最後のページにコメントがまだ出てない場合（figlistが偶数の場合）
    if len(figlist) % 2 == 0:
        wrapped_comment = "\n".join([comment[i:i+48] for i in range(0, len(comment), 48)])
        c.setFont("IPAexGothic", 12)
        icon_width = 25
        icon_height = 25
        c.drawImage(icon_path, 50, height - 70, width=icon_width, height=icon_height, mask='auto')
        c.drawString(70, height - 70, "  コメント")
        text = c.beginText(50, height - 100)
        text.setFont("IPAexGothic", 10)
        text.setLeading(14)
        for line in wrapped_comment.splitlines():
            text.textLine(line)
        c.drawText(text)
        c.showPage()

    c.save()
    pdf_output.seek(0)
    return pdf_output



        
# タブを作成
tab1, tab2, tab3 = st.tabs(["グラフ", "ID入力", "テストデータ入力"])

with tab1:
    # セッションステートの初期化
    if 'additional_count' not in st.session_state:
        st.session_state.additional_count = 0
        
    if st.button("データを更新"):
        conn = sqlite3.connect('physical_rawdata.db')
        rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
        conn.close()
        st.success("データが更新されました")
        
    rawdata_original['date'] = pd.to_datetime(rawdata_original['date'])  # 例: 2025/04/13 形式

    id_list_unique = id_list.drop_duplicates(subset=['ID'])  # ID列で重複を削除
    rawdata = rawdata_original.merge(id_list_unique[['ID', '名前']], on='ID', how='left')
    # データを表示
    st.write(rawdata)
    
    

    st.title("Plot Physical Data")
        
    # 名前とTest Itemの選択
    names = rawdata['名前'].unique()
    test_items = rawdata['Test Item'].unique()

    selected_name = st.selectbox("名前を選択", names)
    selected_eng_name = id_list.loc[id_list['名前'] == selected_name, 'Name'].values[0]
    selected_test = st.selectbox("Test種目を選択", test_items)

    # フィルタリング
    filtered = rawdata[
        (rawdata['名前'] == selected_name) &
        (rawdata['Test Item'] == selected_test)
    ]
    
    
    
    def plot_trendline(rawdata, selected_name, n, additional_test):
        filtered = rawdata[
            (rawdata['名前'] == selected_name) &
            (rawdata['Test Item'] == additional_test)
        ]

        if filtered.empty:
            st.warning(f"該当データがありません ({n})")
        else:
            filtered = filtered.sort_values(by='date')
            X = pd.to_datetime(filtered['date']).map(pd.Timestamp.toordinal)
            X = sm.add_constant(X)
            y = filtered['Result']

            model = sm.OLS(y, X)
            results = model.fit()
            filtered['trendline'] = results.predict(X)

            fig = px.line(
                filtered, x='date', y='Result', markers=True,
                title=additional_test,
                labels={"date": "date", "Result": "Result"}
            )
            fig.add_scatter(
                x=filtered['date'], y=filtered['trendline'],
                mode='lines', name='',
                line=dict(color='orange', dash='dot')
            )

            st.plotly_chart(fig, use_container_width=True, key=f"chart_{n}")
            return fig  # 追加：生成したfigを返す





    if filtered.empty:
        st.warning("該当データがありません")
    else:
        # 最初のグラフ（メインのテスト種目）
        fig = plot_trendline(rawdata, selected_name, 0, selected_test)
        figlist = [fig]  
        
     # 追加グラフ描画ループ
    for i in range(st.session_state.additional_count):
        selected = st.selectbox(
            f"追加テスト種目 {i+1}", test_items,
            key=f"additional_test_{i}"
        )
        fig = plot_trendline(rawdata, selected_name, i+1, selected)
        figlist.append(fig)  
        

    # グラフ追加ボタン（ページの一番下にくる）
    if st.button("グラフを追加"):
        st.session_state.additional_count += 1
        st.rerun()
    
    
        
    comment = st.text_area('📝コメント', height=200)
    
    
    

    
    if st.button("PDFを出力"):
        # PDFをメモリ上で生成
        pdf_data = save_plots_to_pdf(figlist, selected_eng_name, selected_name, comment)
        st.success("PDFが生成されました")
        output_path = st.text_input("保存先のファイル名を入力してください", "output_plots.pdf")


        # PDFをダウンロードボタンで提供
        st.download_button(
            label="PDFをダウンロード",
            data=pdf_data,
            file_name=output_path,
            mime="application/pdf"
        )



        

with tab2:
    st.header("ID入力")
    st.write("現在のIDリスト:")
    st.write(id_list)

    st.write("IDリストの更新:")
    with st.form("id_form"):
        new_name = st.text_input("新しい名前(ja)を入力")
        new_eng_name = st.text_input("新しい名前(eng)を入力")
        new_id = st.text_input("新しいIDを入力")
        submitted = st.form_submit_button("追加")
        if submitted:
            conn = sqlite3.connect('id_database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO id_table (名前, Name, ID) VALUES (?, ?, ?)", (new_name, new_eng_name, new_id))
            conn.commit()
            conn.close()
            st.success("新しいIDが追加されました")
            
        st.write("最新のIDリストを再表示:")
        id_list = pd.read_sql_query("SELECT * FROM id_table", sqlite3.connect('id_database.db'))
        st.write(id_list)
    # 一番下の行を削除するボタンをフォーム外に移動
    st.write("一番下の行を削除するには以下のボタンを押してください:")
    if st.button("一番下の行を削除"):
        conn = sqlite3.connect('id_database.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM id_table WHERE rowid = (SELECT MAX(rowid) FROM id_table)")
        conn.commit()
        conn.close()
        st.success("一番下の行が削除されました")
        # 最新のIDリストを再表示
        id_list = pd.read_sql_query("SELECT * FROM id_table", sqlite3.connect('id_database.db'))
        st.write(id_list)
        

with tab3:
    st.header("テストデータ入力")
    
    with st.form("test_data_form"):
        test_name = st.text_input("名前(ja)を選択")
        test_date = st.date_input("日付を入力")
        test_pos = st.selectbox('ポジションを選択', ['P', 'C', 'IF', 'OF'])
        test_item = st.selectbox("Test Itemを選択", rawdata_original['Test Item'].unique())
        test_result = st.text_input("結果を入力")
        submitted = st.form_submit_button("追加")
        
        
        
        if submitted:
            if test_name not in id_list['名前'].values:
                st.warning("入力された名前はIDリストに存在しません")
                st.stop()
            else:
                test_eng_name = id_list.loc[id_list['名前'] == test_name, 'Name'].values[0]
                test_id = id_list.loc[id_list['名前'] == test_name, 'ID'].values[0]
                test_id = int(test_id)
                test_name_2 = f'{test_pos}_{test_name}'
            
            try:
                float(test_result)
            except ValueError:
                st.warning("結果は数値型で入力してください")
                st.stop()
                
            
                
            conn = sqlite3.connect('physical_rawdata.db')
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO physical_rawdata (Name_1, date, ID, Name_2, Position, [Test Item], Result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (test_eng_name, test_date, test_id, test_name_2, test_pos, test_item, test_result))
            conn.commit()
            conn.close()
            st.success("新しいテストデータが追加されました")
            
            
            
            conn = sqlite3.connect('physical_rawdata.db')
            rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
            conn.close()
            
            st.write(rawdata_original)
       
        
    st.write("一番下の行を削除するには以下のボタンを押してください:")
    if st.button("一番下の行を削除 (テストデータ)"):
        conn = sqlite3.connect('physical_rawdata.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM physical_rawdata WHERE rowid = (SELECT MAX(rowid) FROM physical_rawdata)")
        conn.commit()
        conn.close()
        st.success("一番下の行が削除されました")
        # 最新のテストデータを再表示
        conn = sqlite3.connect('physical_rawdata.db')
        rawdata_original = pd.read_sql_query("SELECT * FROM physical_rawdata", conn)
        conn.close()
        st.write(rawdata_original)
            
      
        
        

        