import streamlit as st
from datetime import datetime

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. データベース・価格設定 ---
@st.cache_resource
def get_database():
    return {"orders": [], "order_count": 0}

db = get_database()

# 商品ごとの価格設定
PRICES = {
    "🍋【ドリンク】ひとつぶレモネード": 300,
    "🫐【ドリンク】ブルーベリースムージー": 300,
    "🍵【ドリンク】抹茶ラテ": 300,
    "🥣【甘味】ぜんざい": 200,
    "🥭【甘味】マンゴープリン": 200,
    "🍠【甘味】大学いも": 200,
    "🍡【甘味】五大くずもち": 200,
    "🍉【甘味】カットスイカ": 100,
    "🍗【つまみ】唐揚げ": 100,
    "🫛【つまみ】枝豆": 100,
    "🥔【つまみ】ハッシュドポテト": 100,
    "🥒【つまみ】カップきゅうり": 100,
    "🥟【つまみ】カップ餃子": 100
}

st.set_page_config(page_title="模擬店オーダーシステム", page_icon="🍔", layout="wide")

# --- 全体のデザイン調整 ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        
        /* ======== ボタンの文字とサイズ調整 ======== */
        div[data-testid="stButton"] button {
            height: auto !important;
            min-height: 2.8rem !important;
            padding: 0.3rem !important;
        }
        
        div[data-testid="stButton"] button p {
            font-size: 1.2rem !important;
            font-weight: bold !important;
            white-space: normal !important;
            word-break: keep-all !important;
            line-height: 1.2 !important;
            margin: 0 !important;
        }
        
        /* 合計金額表示用 */
        .total-price-box {
            background-color: #ffe6e6;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
            border: 2px solid #ff4b4b;
        }
        .total-price-text {
            font-size: 2rem;
            font-weight: bold;
            color: #ff4b4b;
            margin: 0;
        }
    </style>
""", unsafe_allow_html=True)

# メニューリスト
MENU_DRINK = ["🍋【ドリンク】ひとつぶレモネード", "🫐【ドリンク】ブルーベリースムージー", "🍵【ドリンク】抹茶ラテ"]
MENU_SWEET = ["🥣【甘味】ぜんざい", "🥭【甘味】マンゴープリン", "🍠【甘味】大学いも", "🍡【甘味】五大くずもち", "🍉【甘味】カットスイカ"]
MENU_SNACK = ["🍗【つまみ】唐揚げ", "🫛【つまみ】枝豆", "🥔【つまみ】ハッシュドポテト", "🥒【つまみ】カップきゅうり", "🥟【つまみ】カップ餃子"]
MENU = MENU_DRINK + MENU_SWEET + MENU_SNACK

mode = st.sidebar.radio("役割（画面）を選んでください", ["🛒 受付（レジ）", "🍳 調理場（キッチン）"])

# ==========================================
# 🛒 受付（レジ）画面
# ==========================================
if mode == "🛒 受付（レジ）":
    st.title("🛒 受付レジ画面")
    
    with st.expander("⚙️ システム設定（危険）"):
        if st.button("⚠️ 注文番号と履歴をすべてリセットする"):
            db["order_count"] = 0
            db["orders"] = []
            if "cart" in st.session_state:
                st.session_state.cart = {}
            st.success("すべてのデータをリセットしました！")
            st.rerun()

    if "cart" not in st.session_state:
        st.session_state.cart = {}

    tab_order, tab_status, tab_sales = st.tabs(["🛒 注文・お会計", "📋 注文状況・訂正", "📊 売上集計"])

    with tab_order:
        st.subheader("1. 注文を選択")
        
        t_drink, t_sweet, t_snack = st.tabs(["🥤 ドリンク", "🍡 甘味", "🍗 つまみ"])
        
        with t_drink:
            for item in MENU_DRINK:
                if st.button(f"{item} ({PRICES[item]}円)", key=f"btn_{item}", use_container_width=True):
                    st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1
        with t_sweet:
            for item in MENU_SWEET:
                if st.button(f"{item} ({PRICES[item]}円)", key=f"btn_{item}", use_container_width=True):
                    st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1
        with t_snack:
            for item in MENU_SNACK:
                if st.button(f"{item} ({PRICES[item]}円)", key=f"btn_{item}", use_container_width=True):
                    st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1

        st.divider()
        
        st.subheader("2. お会計・カートの確認")
        cart_items = {k: v for k, v in st.session_state.cart.items() if v > 0}
        
        if len(cart_items) > 0:
            total_amount = 0
            
            for item, count in cart_items.items():
                item_price = PRICES[item]
                subtotal = item_price * count
                total_amount += subtotal
                
                st.markdown(
                    f"<div style='font-size: 1.3rem; line-height: 1.4; margin-bottom: 5px;'>"
                    f"<b>{item}</b><br>"
                    f"{item_price}円 × {count}個 ＝ <b>{subtotal:,}円</b>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                
                # 半分ずつの幅で下に配置
                col_minus, col_plus = st.columns(2)
                with col_minus:
                    if st.button("➖", key=f"minus_{item}", use_container_width=True):
                        st.session_state.cart[item] -= 1
                        st.rerun()
                with col_plus:
                    if st.button("➕", key=f"plus_{item}", use_container_width=True):
                        st.session_state.cart[item] += 1
                        st.rerun()
                st.write("") 
            
            st.markdown(f"""
                <div class="total-price-box">
                    <p style="margin: 0; color: #ff4b4b; font-size: 1.2rem;">お会計合計</p>
                    <p class="total-price-text">{total_amount:,} 円</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚀 注文を送信", type="primary", use_container_width=True):
                    db["order_count"] += 1
                    
                    uid = db["order_count"]
                    display_id = uid % 30
                    if display_id == 0:
                        display_id = 30

                    new_order = {
                        "uid": uid,
                        "display_id": display_id,
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "items": cart_items.copy(),
                        "total_amount": total_amount, 
                        "status": "調理待ち", 
                        "is_revised": False,
                        "revision_count": 0,
                        "diff_msg": ""
                    }
                    db["orders"].insert(0, new_order)
                    st.session_state.cart = {}
                    st.success(f"【 {new_order['display_id']} 番 】の注文（{total_amount:,}円）を送信しました！")
                    st.rerun()
            with col_btn2:
                if st.button("🗑️ 空にする", use_container_width=True):
                    st.session_state.cart = {}
                    st.rerun()
        else:
            st.info("商品は選択されていません。")

    with tab_status:
        st.subheader("📝 注文状況・訂正")
        
        if st.button("🔄 最新の調理状況を確認する", use_container_width=True):
            st.rerun()
            
        if not db["orders"]:
            st.write("送信された注文はありません。")
        else:
            for order in db["orders"]:
                if order["status"] == "調理完了":
                    with st.expander(f"✅ 番号 {order['display_id']} : 調理完了 ({order.get('total_amount', 0):,}円)"):
                        for item, count in order["items"].items():
                            st.write(f" - {item} : {count}個")
                else:
                    with st.expander(f"番号 {order['display_id']} (現在の状態: {order['status']}) を訂正"):
                        edit_key = f"edit_{order['uid']}"
                        if edit_key not in st.session_state:
                            st.session_state[edit_key] = order["items"].copy()
                        
                        st.write("▼数量を変更して「訂正を送信」を押してください")
                        for item in MENU:
                            current_val = st.session_state[edit_key].get(item, 0)
                            # チェックボックスで商品を追加するか、既に1個以上ある場合
                            if current_val > 0 or st.checkbox(f"{item} を追加", key=f"chk_{order['uid']}_{item}"):
                                st.markdown(f"**{item}** : {current_val} 個")
                                
                                # 訂正画面でも下に「➖」「➕」を配置するスタイルに変更
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.button("➖", key=f"edit_minus_{order['uid']}_{item}", use_container_width=True):
                                        if st.session_state[edit_key][item] > 0:
                                            st.session_state[edit_key][item] -= 1
                                            st.rerun()
                                with c2:
                                    if st.button("➕", key=f"edit_plus_{order['uid']}_{item}", use_container_width=True):
                                        st.session_state[edit_key][item] = current_val + 1
                                        st.rerun()
                                st.write("")

                        if st.button("🔄 この内容で訂正を送信", key=f"btn_edit_{order['uid']}", type="primary", use_container_width=True):
                            old_items = order["items"].copy()
                            new_items = {k: v for k, v in st.session_state[edit_key].items() if v > 0}
                            
                            diffs = []
                            all_keys = set(old_items.keys()) | set(new_items.keys())
                            for k in all_keys:
                                old_v = old_items.get(k, 0)
                                new_v = new_items.get(k, 0)
                                if old_v != new_v:
                                    if new_v == 0: diffs.append(f"❌ {k} (削除)")
                                    elif old_v == 0: diffs.append(f"➕ {k} (追加: {new_v}個)")
                                    else: diffs.append(f"🔄 {k} ({old_v}個 ➡️ {new_v}個)")
                            
                            if diffs:
                                new_total = sum(PRICES[k] * v for k, v in new_items.items())
                                
                                order["items"] = new_items
                                order["total_amount"] = new_total
                                order["is_revised"] = True
                                order["revision_count"] = order.get("revision_count", 0) + 1 
                                order["diff_msg"] = "\n".join(diffs)
                                order["status"] = "調理待ち" 
                                st.success("訂正を送信しました！")
                                st.rerun()
                            else:
                                st.warning("変更がありませんでした。")

    with tab_sales:
        st.subheader("📊 商品ごとの売上・金額集計")
        st.write("※訂正・取り消しが行われた場合、ここの集計数や金額も自動で計算し直されます。")
        st.write("") 
        
        sales_counts = {item: 0 for item in MENU}
        for o in db["orders"]:
            for item, count in o["items"].items():
                if item in sales_counts:
                    sales_counts[item] += count
        
        col1, col2 = st.columns(2)
        total_revenue = 0
        
        for i, item in enumerate(MENU):
            display_name = item
            target = 20 
            
            if "】" in item:
                emoji = item.split("【")[0]
                name = item.split("】")[1]
                display_name = f"{emoji} {name}"
                
            if "【つまみ】" in item:
                target = 30
                
            current_count = sales_counts[item]
            item_revenue = current_count * PRICES[item]
            total_revenue += item_revenue
            
            display_text = f"#### {display_name}\n販売数: **{current_count}** 個 ({current_count} / {target})<br>売上額: **{item_revenue:,}円**"
            
            if i % 2 == 0:
                with col1:
                    st.markdown(display_text, unsafe_allow_html=True)
            else:
                with col2:
                    st.markdown(display_text, unsafe_allow_html=True)
                    
        st.divider()
        st.markdown(f"<h2 style='text-align: center;'>💰 模擬店 総売上金額: {total_revenue:,} 円</h2>", unsafe_allow_html=True)


# ==========================================
# 🍳 調理場（キッチン）画面
# ==========================================
elif mode == "🍳 調理場（キッチン）":
    st.title("🍳 調理場画面")
    
    if st_autorefresh:
        st_autorefresh(interval=5000, key="kitchen_refresh")
        
    current_kitchen_state = {o["uid"]: o.get("revision_count", 0) for o in db["orders"] if o["status"] == "調理待ち"}
    
    if "known_kitchen_state" not in st.session_state:
        st.session_state.known_kitchen_state = current_kitchen_state.copy()
        
    play_new_sound = False
    play_rev_sound = False
        
    for uid, current_rev_count in current_kitchen_state.items():
        display_id = next((o["display_id"] for o in db["orders"] if o["uid"] == uid), uid)
        
        if uid not in st.session_state.known_kitchen_state:
            st.toast(f"🔔 新規注文（番号: {display_id}）が入りました！", icon="🔥")
            play_new_sound = True
            
        elif current_rev_count > st.session_state.known_kitchen_state[uid]:
            st.toast(f"⚠️ 番号 {display_id} に訂正が入りました！", icon="⚠️")
            play_rev_sound = True
            
    st.session_state.known_kitchen_state = current_kitchen_state.copy()

    # --- 通知音を鳴らす処理 ---
    if play_new_sound:
        st.markdown(
            """
            <audio autoplay>
                <source src="https://assets.mixkit.co/active_storage/sfx/2870/2870-preview.mp3" type="audio/mpeg">
            </audio>
            """,
            unsafe_allow_html=True
        )
    elif play_rev_sound:
        st.markdown(
            """
            <audio autoplay>
                <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
            </audio>
            """,
            unsafe_allow_html=True
        )

    if st.button("🔄 最新の状況を手動で確認する", use_container_width=True):
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["🔥 調理待ち", "✅ 調理完了リスト", "📊 売上集計"])
    
    with tab1:
        active_orders = sorted([o for o in db["orders"] if o["status"] == "調理待ち"], key=lambda x: x["uid"])
        
        if len(active_orders) == 0:
            st.success("現在、調理待ちの注文はありません！🎉")
        else:
            for o in active_orders:
                if o["is_revised"]:
                    st.error("⚠️ 【訂正が入りました！】")
                    st.markdown(f"**変更内容:**\n{o['diff_msg']}")
                
                with st.container(border=True):
                    st.markdown(f"# 🧾 番号: {o['display_id']}")
                    st.write(f"時間: {o['time']}")
                    
                    for item, count in o["items"].items():
                        st.markdown(f"### 🔸 {item} ： **{count}** 個")
                    
                    if st.button(f"✅ 調理完了にする", key=f"kitchen_done_{o['uid']}", type="primary", use_container_width=True):
                        o["status"] = "調理完了"
                        o["is_revised"] = False 
                        st.rerun()
                st.write("") 
                
        st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)

    with tab2:
        done_orders = [o for o in db["orders"] if o["status"] == "調理完了"]
        if not done_orders:
            st.write("完了した注文はありません。")
        for o in done_orders:
            st.success(f"✅ 番号: {o['display_id']} (調理完了)")
            for item, count in o["items"].items():
                st.write(f" - {item}: {count}個")
            st.divider()
            
    with tab3:
        st.subheader("📊 商品ごとの売上・金額集計")
        st.write("※訂正・取り消しが行われた場合、ここの集計数や金額も自動で計算し直されます。")
        st.write("") 
        
        sales_counts = {item: 0 for item in MENU}
        for o in db["orders"]:
            for item, count in o["items"].items():
                if item in sales_counts:
                    sales_counts[item] += count
        
        col1, col2 = st.columns(2)
        total_revenue = 0
        
        for i, item in enumerate(MENU):
            display_name = item
            target = 20 
            
            if "】" in item:
                emoji = item.split("【")[0]
                name = item.split("】")[1]
                display_name = f"{emoji} {name}"
                
            if "【つまみ】" in item:
                target = 30
                
            current_count = sales_counts[item]
            item_revenue = current_count * PRICES[item]
            total_revenue += item_revenue
            
            display_text = f"#### {display_name}\n販売数: **{current_count}** 個 ({current_count} / {target})<br>売上額: **{item_revenue:,}円**"
            
            if i % 2 == 0:
                with col1:
                    st.markdown(display_text, unsafe_allow_html=True)
            else:
                with col2:
                    st.markdown(display_text, unsafe_allow_html=True)
                    
        st.divider()
        st.markdown(f"<h2 style='text-align: center;'>💰 模擬店 総売上金額: {total_revenue:,} 円</h2>", unsafe_allow_html=True)
