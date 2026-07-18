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

# メニューリストの更新
MENU = [
    "🍋【ドリンク】ひとつぶレモネード", "🫐【ドリンク】ブルーベリースムージー", "🍵【ドリンク】抹茶ラテ",
    "🥣【甘味】ぜんざい", "🥖【甘味】チュロス", "🥭【甘味】マンゴープリン", "🍠【甘味】大学いも", "🍡【甘味】五大くずもち",
    "🍗【つまみ】唐揚げ", "🫛【つまみ】枝豆", "🥔【つまみ】ハッシュドポテト", "🥒【つまみ】カップきゅうり", "🥟【つまみ】カップ餃子"
]

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

    st.subheader("1. 注文を入力")
    cols = st.columns(2)
    for i, item in enumerate(MENU):
        with cols[i % 2]:
            if st.button(item, use_container_width=True):
                st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1

    st.divider()
    
    st.subheader("2. カートの確認")
    cart_items = {k: v for k, v in st.session_state.cart.items() if v > 0}
    
    if len(cart_items) > 0:
        for item, count in cart_items.items():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"#### {item}： **{count}** 個")
            with col2:
                if st.button("➖", key=f"minus_{item}"):
                    st.session_state.cart[item] -= 1
                    st.rerun()
            with col3:
                if st.button("➕", key=f"plus_{item}"):
                    st.session_state.cart[item] += 1
                    st.rerun()
                
        col_btn1, col_btn2 = st.columns(2)
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
                    "diff_msg": ""
                }
                db["orders"].insert(0, new_order)
                st.session_state.cart = {}
                st.success(f"【 {new_order['display_id']} 番 】を送信しました！")
                st.rerun()
        with col_btn2:
            if st.button("🗑️ カートを空にする", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
    else:
        st.info("商品は選択されていません。")

    st.divider()
    
    st.subheader("📝 注文状況・訂正")
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
                                new_val = st.number_input("個数", min_value=0, value=current_val, key=f"num_{order['uid']}_{item}")
                                st.session_state[edit_key][item] = new_val

                    if st.button("🔄 この内容で訂正を送信", key=f"btn_edit_{order['uid']}", type="primary"):
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
        
    current_kitchen_state = {o["uid"]: o["is_revised"] for o in db["orders"] if o["status"] == "調理待ち"}
    
    if "known_kitchen_state" not in st.session_state:
        st.session_state.known_kitchen_state = current_kitchen_state.copy()
        
    for uid, is_rev in current_kitchen_state.items():
        display_id = next((o["display_id"] for o in db["orders"] if o["uid"] == uid), uid)
        if uid not in st.session_state.known_kitchen_state:
            st.toast(f"🔔 新規注文（番号: {display_id}）が入りました！", icon="🔥")
        elif is_rev and not st.session_state.known_kitchen_state[uid]:
            st.toast(f"⚠️ 番号 {display_id} に訂正が入りました！", icon="⚠️")
            
    st.session_state.known_kitchen_state = current_kitchen_state.copy()

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

    with tab2:
        done_orders = [o for o in db["orders"] if o["status"] == "調理完了"]
        if not done_orders:
            st.write("完了した注文はありません。")
        for o in done_orders:
            st.success(f"✅ 番号: {o['display_id']} (調理完了)")
            for item, count in o["items"].items():
                st.write(f" - {item}: {count}個")
            st.divider()
