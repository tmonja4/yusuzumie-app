import streamlit as st
from datetime import datetime

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. データベース設定 ---
@st.cache_resource
def get_database():
    return {"orders": [], "order_count": 0}

db = get_database()

st.set_page_config(page_title="模擬店オーダーシステム", page_icon="🍔", layout="wide")

# --- 全体のデザイン調整（スマホでの横並び強制・省スペース化） ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        
        /* スマホ画面（幅576px以下）のレイアウト強制調整 */
        @media (max-width: 576px) {
            /* カラムの自動縦並び（スタック）を無効化し、常に横並びをキープする */
            div[data-testid="stHorizontalBlock"] {
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: center !important;
            }
            /* 1つ目のカラム（商品名やメインボタン）の幅を広く確保 */
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {
                flex: 5 !important;
                width: auto !important;
                min-width: 0 !important;
            }
            /* 2つ目・3つ目のカラム（＋・ーボタンなど）はコンパクトに */
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(n+2) {
                flex: 2 !important;
                width: auto !important;
                min-width: 0 !important;
                padding-left: 0.2rem !important;
                padding-right: 0.2rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# メニューリスト（カテゴリ別に分割）
MENU_DRINK = ["🍋【ドリンク】ひとつぶレモネード", "🫐【ドリンク】ブルーベリースムージー", "🍵【ドリンク】抹茶ラテ"]
MENU_SWEET = ["🥣【甘味】ぜんざい", "🥖【甘味】チュロス", "🥭【甘味】マンゴープリン", "🍠【甘味】大学いも", "🍡【甘味】五大くずもち"]
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

    tab_order, tab_status = st.tabs(["🛒 注文入力", "📋 注文状況・訂正"])

    with tab_order:
        st.subheader("1. 注文を選択")
        
        t_drink, t_sweet, t_snack = st.tabs(["🥤 ドリンク", "🍡 甘味", "🍗 つまみ"])
        
        with t_drink:
            for item in MENU_DRINK:
                if st.button(item, use_container_width=True):
                    st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1
        with t_sweet:
            for item in MENU_SWEET:
                if st.button(item, use_container_width=True):
                    st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1
        with t_snack:
            for item in MENU_SNACK:
                if st.button(item, use_container_width=True):
                    st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1

        st.divider()
        
        st.subheader("2. カートの確認")
        cart_items = {k: v for k, v in st.session_state.cart.items() if v > 0}
        
        if len(cart_items) > 0:
            for item, count in cart_items.items():
                col1, col2, col3 = st.columns([5, 2, 2])
                with col1:
                    # 縦幅を削減するためにHTMLで少しコンパクトに表示
                    st.markdown(f"<div style='line-height: 1.2; padding-top: 0.5rem;'><b>{item}</b><br><small>数量: <b>{count}</b> 個</small></div>", unsafe_allow_html=True)
                with col2:
                    if st.button("➖", key=f"minus_{item}", use_container_width=True):
                        st.session_state.cart[item] -= 1
                        st.rerun()
                with col3:
                    if st.button("➕", key=f"plus_{item}", use_container_width=True):
                        st.session_state.cart[item] += 1
                        st.rerun()
            
            st.write("")
            col_btn1, col_btn2 = st.columns([2, 1])
            with col_btn1:
                if st.button("🚀 注文を送信", type="primary", use_container_width=True):
                    db["order_count"] += 1
                    
                    uid = db["order_count"]
                    display_id = uid % 20
                    if display_id == 0:
                        display_id = 20

                    new_order = {
                        "uid": uid,
                        "display_id": display_id,
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "items": cart_items.copy(),
                        "status": "調理待ち", 
                        "is_revised": False,
                        "revision_count": 0,
                        "diff_msg": ""
                    }
                    db["orders"].insert(0, new_order)
                    st.session_state.cart = {}
                    st.success(f"【 {new_order['display_id']} 番 】を送信しました！")
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
                    with st.expander(f"✅ 番号 {order['display_id']} : 調理完了"):
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
                            if current_val > 0 or st.checkbox(f"{item} を追加", key=f"chk_{order['uid']}_{item}"):
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    st.write(item)
                                with c2:
                                    # ラベルを非表示にして縦スペースを節約し、横並びを綺麗にする
                                    new_val = st.number_input("個数", min_value=0, value=current_val, key=f"num_{order['uid']}_{item}", label_visibility="collapsed")
                                    st.session_state[edit_key][item] = new_val

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
                                order["items"] = new_items
                                order["is_revised"] = True
                                order["revision_count"] = order.get("revision_count", 0) + 1 
                                order["diff_msg"] = "\n".join(diffs)
                                order["status"] = "調理待ち" 
                                st.success("訂正を送信しました！")
                                st.rerun()
                            else:
                                st.warning("変更がありませんでした。")

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

    if st.button("🔄 最新の注文を手動で確認する", use_container_width=True):
        st.rerun()

    tab1, tab2 = st.tabs(["🔥 調理待ち", "✅ 調理完了リスト"])
    
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
                
        # --- 下側の見やすさを確保するための余白 ---
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
